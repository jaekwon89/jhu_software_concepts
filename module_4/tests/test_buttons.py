import pytest
import app.routes as routes
import app.db as db
from app.db_helper import insert_records_by_url
from load_data import data_type


def _fake_rows():
    return [
        {
            "program": "Computer Science, Johns Hopkins University",
            "comments": "row A",
            "date_added": "September 05, 2025",
            "url": "https://www.thegradcafe.com/result/7001",
            "status": "Accepted on 09/05/2025",
            "term": "Fall 2025",
            "US/International": "International",
            "GRE": "169",
            "GRE_V": "164",
            "GRE_AW": "5.0",
            "GPA": "GPA 3.95",
            "Degree": "Masters",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Johns Hopkins University",
        }
    ]


def _install_sync_worker(monkeypatch, rows):
    # Make /pull-data run synchronously (triggers “loader” deterministically)
    def fake_run_pipeline(*_a, **_k):
        inserted = insert_records_by_url(rows, data_type)
        return {
            "cleaned": len(rows),
            "llm": len(rows),
            "inserted": inserted,
            "message": "ok",
        }

    class FakeThread:
        def __init__(self, target, args=(), daemon=None):
            self._target, self._args = target, args

        def start(self):  # run immediately
            self._target(*self._args)

    monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(routes.threading, "Thread", FakeThread)
    routes._pull_running.clear()


@pytest.mark.buttons
def test_pull_data_returns_200_when_not_busy_and_triggers_loader(client, monkeypatch):
    rows = _fake_rows()
    _install_sync_worker(monkeypatch, rows)

    # before: empty
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == 0

    # Spec wants 200 – follow the redirect to land back on a page with 200
    r = client.post("/pull-data", follow_redirects=True)
    assert r.status_code == 200

    # after: rows inserted (loader triggered)
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == len(rows)


@pytest.mark.buttons
def test_update_analysis_returns_200_when_not_busy(client):
    r = client.post("/update-analysis", follow_redirects=True)
    assert r.status_code == 200


@pytest.mark.buttons
def test_busy_gating_pull_data_returns_409(client):
    routes._pull_running.set()
    r = client.post("/pull-data")
    assert r.status_code == 409
    assert r.is_json and r.get_json().get("busy") is True
    routes._pull_running.clear()


@pytest.mark.buttons
def test_busy_gating_update_analysis_returns_409(client):
    routes._pull_running.set()
    r = client.post("/update-analysis")
    assert r.status_code == 409
    assert r.is_json and r.get_json().get("busy") is True
    routes._pull_running.clear()
