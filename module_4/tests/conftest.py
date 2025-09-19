# Conftest

import pytest
from app import create_app
import app.db as db
import app.routes as routes
from app.db_helper import insert_records_by_url
from load_data import data_type


@pytest.fixture(autouse=True)
def stub_queries(monkeypatch):
    def patch(name, value):
        if hasattr(routes.query_data, name):
            monkeypatch.setattr(routes.query_data, name, value)
    patch("count_fall_2025", lambda: 1)
    patch("percent_international", lambda: {"international_count": 1, "us_count": 1, "other_count": 0})
    patch("avg_scores", lambda: {"avg_gpa": 3.4, "avg_gre": 165, "avg_gre_v": 158, "avg_gre_aw": 4.5})
    patch("avg_gpa_american_fall2025", lambda: 3.2)
    patch("acceptance_rate_fall2025", lambda: 37.12)
    patch("avg_gpa_fall2025_acceptances", lambda: 3.6)
    patch("count_jhu_masters_cs", lambda: 7)
    patch("count_gt_phd_accept", lambda: 2)
    patch("degree_counts_2025", lambda: [("Masters", 10)])
    patch("top_5_programs", lambda: [("CS", 8)])
    
# ---------------------------
# Flask app & client
# ---------------------------
@pytest.fixture
def app():
    from app import create_app
    app_instance = create_app()
    app_instance.config["TESTING"] = True        # <— important
    yield app_instance


@pytest.fixture
def client(app):
    """Flask test client (use follow_redirects=True in tests when needed)."""
    return app.test_client()



# ---------------------------
# DB isolation
# ---------------------------
@pytest.fixture(autouse=True)
def clean_db():
    """Truncate applicants table before and after each test."""
    db.ensure_table()
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()
    yield
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()


# ---------------------------
# Pipeline/thread stubbing
# ---------------------------
@pytest.fixture
def install_sync_pipeline(monkeypatch):
    """
    Return a helper that makes /pull-data run synchronously:
      - run_pipeline is stubbed to insert provided rows using real insert function
      - background Thread is replaced by a FakeThread that runs immediately
      - busy flag is cleared
    Usage:
        rows = [...]
        install_sync_pipeline(rows)
    """
    def _install(rows):
        def fake_run_pipeline(*_a, **_k):
            inserted = insert_records_by_url(rows, data_type)
            return {"cleaned": len(rows), "llm": len(rows), "inserted": inserted, "message": "ok"}

        monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)

        class FakeThread:
            def __init__(self, target, args=(), daemon=None):
                self._target, self._args = target, args
            def start(self):
                self._target(*self._args)

        monkeypatch.setattr(routes.threading, "Thread", FakeThread)
        routes._pull_running.clear()  # ensure not busy
    return _install

