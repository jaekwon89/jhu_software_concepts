import pytest
import app.routes as routes
import app.db as db
from app.db_helper import insert_records_by_url
from load_data import data_type

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
            "GRE": "170", "GRE_V": "165", "GRE_AW": "5.0", "GPA": "GPA 3.90",
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
            "GRE": "168", "GRE_V": "162", "GRE_AW": "4.5", "GPA": "GPA 3.70",
            "Degree": "PhD",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Georgetown University",
        },
    ]

def _install_sync_worker(monkeypatch, rows):
    def fake_run_pipeline(*_a, **_k):
        inserted = insert_records_by_url(rows, data_type)
        return {"cleaned": len(rows), "llm": len(rows), "inserted": inserted, "message": "ok"}
    monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)

    class FakeThread:
        def __init__(self, target, args=(), daemon=None):
            self._target, self._args = target, args
        def start(self): self._target(*self._args)

    monkeypatch.setattr(routes.threading, "Thread", FakeThread)
    routes._pull_running.clear()

@pytest.fixture(autouse=True)
def _truncate_table():
    db.ensure_table()
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()
    yield
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()

# a) Insert on pull
@pytest.mark.db
def test_insert_on_pull(client, monkeypatch):
    rows = _fake_llm_rows()
    _install_sync_worker(monkeypatch, rows)

    # before empty
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == 0

    # POST /pull-data -> follow redirect -> 200
    resp = client.post("/pull-data", follow_redirects=True)
    assert resp.status_code == 200

    # rows exist with required non-null fields
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == len(rows)
        cur.execute("""
            SELECT COUNT(*) FROM applicants
            WHERE program IS NOT NULL AND program <> ''
              AND url IS NOT NULL AND url <> ''
              AND status IS NOT NULL AND status <> ''
              AND term IS NOT NULL AND term <> '';
        """)
        assert cur.fetchone()[0] == len(rows)

# b) Idempotency
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
        assert cur.fetchone()[0] == len(rows)  # still 2

# c) Simple query returns expected keys
@pytest.mark.db
def test_simple_query_function_returns_expected_keys(client, monkeypatch):
    rows = _fake_llm_rows()
    _install_sync_worker(monkeypatch, rows)
    client.post("/pull-data", follow_redirects=True)

    import app.query_data as qd
    result = qd.percent_international()
    assert set(result.keys()) == {"international_count", "us_count", "other_count"}
    assert result["international_count"] == 1
    assert result["us_count"] == 1
    assert result["other_count"] == 0