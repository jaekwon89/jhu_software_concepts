# pylint: disable=missing-function-docstring
"""Integration tests for routes + DB write/read flow."""
import pytest

from app import routes  # fixes R0402
import app.db as db
import app.query_data as qd  # keep top-level to avoid C0415
from app.db_helper import insert_records_by_url
from src.load_data import data_type  # avoids E0401 in some setups


def _fake_llm_rows():
    return [
        {
            "program": "Computer Science, Johns Hopkins University",
            "comments": "row A",
            "date_added": "September 05, 2025",
            "url": "https://www.thegradcafe.com/result/1111",
            "status": "Accepted on 09/05/2025",
            "term": "Fall 2025",
            "US/International": "International",
            "GRE": "170",
            "GRE_V": "165",
            "GRE_AW": "5.0",
            "GPA": "GPA 3.90",
            "Degree": "Masters",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Johns Hopkins University",
        },
        {
            "program": "Computer Science, Georgetown University",
            "comments": "row B",
            "date_added": "September 06, 2025",
            "url": "https://www.thegradcafe.com/result/2222",
            "status": "Rejected on 09/06/2025",
            "term": "Fall 2025",
            "US/International": "American",
            "GRE": "168",
            "GRE_V": "162",
            "GRE_AW": "4.5",
            "GPA": "GPA 3.70",
            "Degree": "PhD",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Georgetown University",
        },
    ]


def _clear_busy():
    routes._pull_running.clear()  # pylint: disable=protected-access


def _install_sync_worker(monkeypatch, rows):
    """Patch the async pipeline to run synchronously during tests."""
    def fake_run_pipeline(*_a, **_k):
        inserted = insert_records_by_url(rows, data_type)
        return {"cleaned": len(rows), "llm": len(rows), "inserted": inserted, "message": "ok"}

    monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)

    class FakeThread:
        """A fake Thread that executes its target immediately on start()."""
        def __init__(self, target, args=(), daemon=None):  # pylint: disable=unused-argument
            self._target, self._args = target, args
            self._daemon = daemon  # avoid W0613

        def start(self):
            self._target(*self._args)

    monkeypatch.setattr(routes.threading, "Thread", FakeThread)
    _clear_busy()


@pytest.fixture(autouse=True)
def _truncate_table():
    """Ensure the `applicants` table is empty before and after each test."""
    db.ensure_table()
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()
    yield
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()


@pytest.mark.db
def test_insert_on_pull(client, monkeypatch):
    rows = _fake_llm_rows()
    _install_sync_worker(monkeypatch, rows)

    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == 0

    resp = client.post("/pull-data", follow_redirects=True)
    assert resp.status_code == 200

    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == len(rows)
        cur.execute(
            """
            SELECT COUNT(*) FROM applicants
            WHERE program IS NOT NULL AND program <> ''
              AND url IS NOT NULL AND url <> ''
              AND status IS NOT NULL AND status <> ''
              AND term IS NOT NULL AND term <> '';
            """
        )
        assert cur.fetchone()[0] == len(rows)


@pytest.mark.db
def test_idempotency_no_duplicates_on_second_pull(client, monkeypatch):
    rows = _fake_llm_rows()
    _install_sync_worker(monkeypatch, rows)

    r1 = client.post("/pull-data", follow_redirects=True)
    assert r1.status_code == 200
    r2 = client.post("/pull-data", follow_redirects=True)
    assert r2.status_code == 200

    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == len(rows)


@pytest.mark.db
def test_simple_query_function_returns_expected_keys(client, monkeypatch):
    rows = _fake_llm_rows()
    _install_sync_worker(monkeypatch, rows)
    client.post("/pull-data", follow_redirects=True)

    result = qd.percent_international()
    assert set(result.keys()) == {"international_count", "us_count", "other_count"}
    assert result["international_count"] == 1
    assert result["us_count"] == 1
    assert result["other_count"] == 0
