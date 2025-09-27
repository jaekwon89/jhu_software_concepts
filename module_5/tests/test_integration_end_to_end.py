# pylint: disable=missing-function-docstring
"""Integration tests for the complete data pipeline.

This module contains end-to-end tests that verify the application's core
workflow: pulling data, updating the analysis cache, and rendering the
results. It also tests the idempotency of the data pull mechanism.
"""
# pylint: disable=duplicate-code

import re
import pytest
from app import routes, db  # prefer from-import to satisfy R0402
from app.db_helper import insert_records_by_url
from load_data import data_type


def _fake_rows():
    """Provide a static list of sample applicant data for integration tests."""
    return [
        {
            "program": "Computer Science, Johns Hopkins University",
            "comments": "note A",
            "date_added": "September 05, 2025",
            "url": "https://www.thegradcafe.com/result/9001",
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
        },
        {
            "program": "Computer Science, Georgetown University",
            "comments": "note B",
            "date_added": "September 06, 2025",
            "url": "https://www.thegradcafe.com/result/9002",
            "status": "Rejected on 09/06/2025",
            "term": "Fall 2025",
            "US/International": "American",
            "GRE": "166",
            "GRE_V": "160",
            "GRE_AW": "4.5",
            "GPA": "GPA 3.70",
            "Degree": "PhD",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Georgetown University",
        },
    ]


def _install_sync_pipeline(monkeypatch, rows):
    """Patch the asynchronous data pipeline to run synchronously for testing."""
    def fake_run_pipeline(*_a, **_k):
        inserted = insert_records_by_url(rows, data_type)
        return {
            "cleaned": len(rows),
            "llm": len(rows),
            "inserted": inserted,
            "message": "ok",
        }

    monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)

    class FakeThread:
        """A fake Thread class that executes its target immediately on start()."""
        def __init__(self, target, args=(), daemon=None):
            self._target, self._args = target, args
            self._daemon = daemon  # mark used to avoid W0613 (unused-argument)

        def start(self):
            self._target(*self._args)

    monkeypatch.setattr(routes.threading, "Thread", FakeThread)
    routes._pull_running.clear()  # pylint: disable=protected-access


@pytest.fixture(autouse=True)
def _clean_table():
    """Ensure the `applicants` table is empty before and after each test."""
    db.ensure_table()
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()
    yield
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()


# 5.a End-to-end (pull -> update -> render)
@pytest.mark.integration
def test_end_to_end_pull_update_render(client, monkeypatch):
    """Test the full user workflow: pull data, update analysis, and render page."""
    rows = _fake_rows()
    _install_sync_pipeline(monkeypatch, rows)

    # i) POST /pull-data succeeds and rows are in DB
    r1 = client.post("/pull-data", follow_redirects=True)
    assert r1.status_code == 200
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        assert cur.fetchone()[0] == len(rows)

    # ii) POST /update-analysis succeeds when not busy
    r2 = client.post("/update-analysis", follow_redirects=True)
    assert r2.status_code == 200

    # iii) GET /analysis shows updated analysis and two-decimal percentages
    page = client.get("/analysis")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert re.search(r"Analysis", html, flags=re.IGNORECASE)
    assert re.search(r"\bAnswer:", html, flags=re.IGNORECASE)
    assert re.search(r"\b\d{1,3}\.\d{2}\s*%", html), "Expected two-decimal percentage"


# 5.b Multiple pulls (overlap) respect uniqueness
@pytest.mark.integration
def test_multiple_pulls_respect_uniqueness(client, monkeypatch):
    """Verify that pulling data multiple times does not create duplicate entries."""
    rows = _fake_rows()
    _install_sync_pipeline(monkeypatch, rows)

    r1 = client.post("/pull-data", follow_redirects=True)
    assert r1.status_code == 200
    r2 = client.post("/pull-data", follow_redirects=True)
    assert r2.status_code == 200

    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        # Still equals number of unique URLs
        assert cur.fetchone()[0] == len(rows)
