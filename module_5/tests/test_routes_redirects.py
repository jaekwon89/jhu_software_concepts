"""Tests for the redirect logic of the Flask application routes.

This module contains tests that specifically verify the HTTP 302 redirect
responses from various endpoints under different conditions. It includes
both direct function calls within a test request context and full HTTP
requests made via the test client.
"""

from app import routes  # fixes R0402


def _clear_not_busy():
    """Test helper: force the app into a 'not busy' state for deterministic checks."""
    routes._pull_running.clear()  # pylint: disable=protected-access


def test_index_redirects_function(app):
    """Verify that the index view function returns a 302 redirect to /analysis."""
    with app.test_request_context("/"):
        resp = routes.index()
        assert resp.status_code == 302
        assert resp.location.endswith("/analysis")


def test_update_analysis_redirects_when_not_busy_function(app):
    """Verify update_analysis view function redirects when the system is not busy."""
    _clear_not_busy()
    with app.test_request_context("/update-analysis", method="POST"):
        resp = routes.update_analysis()
        assert resp.status_code == 302
        assert resp.location.endswith("/analysis")


def test_index_redirects_with_client(client):
    """Verify that a GET request to the root URL (/) redirects to /analysis."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/analysis")


def test_update_analysis_redirects_with_client(client):
    """Verify a POST to /update-analysis redirects when the system is not busy."""
    _clear_not_busy()
    r = client.post("/update-analysis", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/analysis")


def test_pull_data_redirects_when_not_busy(client, install_sync_pipeline):
    """Verify POST /pull-data starts the worker and redirects when not busy."""
    _clear_not_busy()
    rows = [
        {
            "url": "https://www.thegradcafe.com/result/123",
            "program": "Computer Science",
            "term": "Fall 2025",
        }
    ]
    install_sync_pipeline(rows)

    resp = client.post("/pull-data", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/analysis")
