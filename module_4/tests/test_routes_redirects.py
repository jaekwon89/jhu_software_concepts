import app.routes as routes


def test_index_redirects_function(app):
    """Covers line ~31 (return redirect to /analysis)."""
    with app.test_request_context("/"):
        resp = routes.index()
        assert resp.status_code == 302
        assert resp.location.endswith("/analysis")


def test_update_analysis_redirects_when_not_busy_function(app):
    """Covers lines ~93–94 (success path: flash + redirect)."""
    routes._pull_running.clear()
    with app.test_request_context("/update-analysis", method="POST"):
        resp = routes.update_analysis()
        assert resp.status_code == 302
        assert resp.location.endswith("/analysis")


def test_index_redirects_with_client(client):
    """Also cover via WSGI client."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/analysis")


def test_update_analysis_redirects_with_client(client):
    """Also cover success path via client."""
    routes._pull_running.clear()
    r = client.post("/update-analysis", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/analysis")


def test_pull_data_redirects_when_not_busy(client, install_sync_pipeline):
    """
    Covers the success branch of /pull-data (lines ~93–94):
    starts the fake worker and returns a redirect to /analysis.
    """
    # Ensure not busy and make the pipeline run synchronously, DB-free
    routes._pull_running.clear()
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
