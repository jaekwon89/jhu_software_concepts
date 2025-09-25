# pylint: disable=missing-function-docstring
"""Unit tests for the routes module."""
import pytest
from app import routes  # fixes R0402: consider-using-from-import
import app.db as db
from app.db_helper import insert_records_by_url
from load_data import data_type


def _fake_rows():
    """Generate a list containing a single, static row of test data."""
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


def _set_busy():
    """Test helper: mark the app as 'busy' (a pull is running)."""
    routes._pull_running.set()  # pylint: disable=protected-access


def _clear_busy():
    """Test helper: mark the app as 'not busy'."""
    routes._pull_running.clear()  # pylint: disable=protected-access


def _install_sync_worker(monkeypatch, rows):
    """Patch the asynchronous data pipeline to run synchronously for testing."""
    def fake_run_pipeline(*_a, **_k):
        inserted = insert_records_by_url(rows, data_type)
        return {"cleaned": len(rows), "llm": len(rows), "inserted": inserted, "message": "ok"}

    class FakeThread:
        """A fake Thread class that executes its target immediately on start()."""

        def __init__(self, target, args=(), daemon=None):  # pylint: disable=unused-argument
            self._target, self._args = target, args
            self._daemon = daemon  # avoid W0613

        def start(self):  # pylint: disable=unused-argument
            self._target(*self._args)

    monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(routes.threading, "Thread", FakeThread)
    _clear_busy()


@pytest.mark.buttons
def test_pull_data_returns_200_when_not_busy_and_triggers_loader(client, monkeypatch):
    """Verify the /pull-data endpoint triggers the data loader and returns 200."""
    rows = _fake_rows()
    _install_sync_worker(monkeypatch, rows)

    # before: empty
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == 0

    # follow the redirect so final response is 200
    r = client.post("/pull-data", follow_redirects=True)
    assert r.status_code == 200

    # after: rows inserted (loader triggered)
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == len(rows)


@pytest.mark.buttons
def test_update_analysis_returns_200_when_not_busy(client):
    """Test that /update-analysis returns 200 OK when the system is not busy."""
    _clear_busy()
    r = client.post("/update-analysis", follow_redirects=True)
    assert r.status_code == 200


@pytest.mark.buttons
def test_busy_gating_pull_data_returns_409(client):
    """Verify that /pull-data returns 409 Conflict when a pull is already running."""
    _set_busy()
    r = client.post("/pull-data")
    assert r.status_code == 409
    assert r.is_json and r.get_json().get("busy") is True
    _clear_busy()


@pytest.mark.buttons
def test_busy_gating_update_analysis_returns_409(client):
    """Verify /update-analysis returns 409 Conflict when a pull is running."""
    _set_busy()
    r = client.post("/update-analysis")
    assert r.status_code == 409
    assert r.is_json and r.get_json().get("busy") is True
    _clear_busy()
