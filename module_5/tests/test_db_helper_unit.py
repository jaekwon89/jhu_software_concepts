# pylint: disable=missing-function-docstring
"""Unit tests for app.db_helper (JSON I/O, RID discovery, inserts)."""

import json
import pytest

import app.db_helper as dh


# ---------- tiny fake DB plumbing ----------

class _FakeCursor:
    """A fake database cursor for testing DB interactions without a real DB.

    Simulates INSERT with a URL uniqueness constraint and fetching preloaded URLs.
    """

    def __init__(self):
        self._seen_urls = set()
        self.rowcount = 0
        self._fetched = []

    # allow: with conn.cursor() as cur:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # pylint: disable=unused-argument
        return False

    # SELECT url FROM applicants -> preload what existing_rids() will fetch
    def preload_urls(self, urls):
        self._fetched = [(u,) for u in urls]

    def execute(self, _sql, params=None):
        """Simulate executing INSERT ... ON CONFLICT (url) DO NOTHING."""
        if params is not None:
            url = params[3]  # url is the 4th value per db_helper column order
            if url not in self._seen_urls:
                self._seen_urls.add(url)
                self.rowcount = 1
            else:
                self.rowcount = 0

    def fetchall(self):
        return list(self._fetched)

    def close(self):  # pragma: no cover
        pass

    @property
    def seen_urls(self):
        """Public accessor used by tests (avoids W0212 on _seen_urls)."""
        return set(self._seen_urls)


class _FakeConn:
    """A fake database connection that uses a _FakeCursor."""

    def __init__(self, cur: _FakeCursor):
        self.cur = cur
        self.commits = 0

    # allow: with pool.connection() as conn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # pylint: disable=unused-argument
        return False

    def cursor(self):
        return self.cur

    def commit(self):
        self.commits += 1


class _FakePool:
    """A fake database connection pool."""

    def __init__(self, cur: _FakeCursor):
        self.cur = cur
        self.last_conn: _FakeConn | None = None

    def connection(self):
        self.last_conn = _FakeConn(self.cur)
        return self.last_conn


def _patch_pool_and_table(monkeypatch, preload_urls=None):
    """Patch db_helper's pool & ensure_table so nothing touches a real DB.

    Optionally preload URLs for existing_rids(). Returns (cursor, fake_pool).
    """
    cur = _FakeCursor()
    if preload_urls is not None:
        cur.preload_urls(preload_urls)
    fake_pool = _FakePool(cur)
    monkeypatch.setattr(dh, "pool", fake_pool)
    monkeypatch.setattr(dh, "ensure_table", lambda: None)
    return cur, fake_pool


# ---------- tests ----------

@pytest.mark.db
def test_read_json_reads_jsonl(tmp_path):
    """read_json should read one JSON object per line (JSONL)."""
    records = [
        {"program": "CS", "url": "https://example/result/1"},
        {"program": "DS", "url": "https://example/result/2"},
    ]
    p = tmp_path / "rows.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    out = dh.read_json(p)
    assert out == records


@pytest.mark.db
def test_write_json_writes_valid_json_array(tmp_path):
    """write_json should write a pretty JSON array that json.load can parse."""
    rows = [
        {"program": "CS", "url": "https://example/result/1"},
        {"program": "DS", "url": "https://example/result/2"},
    ]
    p = tmp_path / "written.json"
    dh.write_json(p, rows)

    with p.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == rows


@pytest.mark.db
def test_existing_rids_parses_ids_from_urls_and_ignores_empty(monkeypatch):
    """existing_rids() drops empty/None and extracts numeric IDs from URLs."""
    preload = [
        None,  # ignored by 'if url:'
        "",    # ignored by 'if url:'
        "https://www.thegradcafe.com/result/123",
        "https://www.thegradcafe.com/result/42?utm=x",
        "https://www.thegradcafe.com/result/9999",
    ]
    _cur, _pool = _patch_pool_and_table(monkeypatch, preload_urls=preload)

    rids = dh.existing_rids()
    assert "123" in rids
    assert "9999" in rids
    assert any(s.startswith("42") for s in rids)  # handle querystring suffix


@pytest.mark.db
def test_insert_records_by_url_counts_only_unique_and_commits(monkeypatch):
    """insert_records_by_url() counts unique URLs and commits once."""
    cur, pool = _patch_pool_and_table(monkeypatch)

    # data_type order must match db_helper.py columns
    def data_type(rec):
        return [
            rec.get("program"),
            None,  # comments
            None,  # date_added
            rec["url"],  # url (index 3)
            None,  # status
            rec.get("term"),
            None,
            None,
            None,
            None,
            None,  # us_or_international, gpa, gre, gre_v, gre_aw, degree
            None,
            rec.get("llm_generated_program"),
            rec.get("llm_generated_university"),
        ]

    rows = [
        {
            "program": "Computer Science",
            "url": "https://www.thegradcafe.com/result/123",
            "term": "Fall 2025",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Johns Hopkins University",
        },
        {  # duplicate URL → ON CONFLICT DO NOTHING
            "program": "Computer Science",
            "url": "https://www.thegradcafe.com/result/123",
            "term": "Fall 2025",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Johns Hopkins University",
        },
    ]

    inserted = dh.insert_records_by_url(rows, data_type)
    assert inserted == 1
    assert cur.seen_urls == {"https://www.thegradcafe.com/result/123"}
    assert pool.last_conn is not None and pool.last_conn.commits == 1
