import pytest
import os

# -------------------------------------------------------------------
# 1) Conditionally configure the database for the test session.
#    This fixture runs once before any tests start.
# -------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _setup_db_for_session():
    # We must use a manually instantiated MonkeyPatch for session-scoped fixtures
    # to avoid a "ScopeMismatch" error.
    mp = pytest.MonkeyPatch()

    if os.getenv("CI") == "true":
        # In the CI environment, we need a real database connection. The app's
        # default pool is created at module import time and is misconfigured
        # for 'localhost'. To fix this, we patch the ConnectionPool class itself.
        import psycopg_pool

        # Keep a reference to the original class for creating our correctly
        # configured pool and for proper cleanup.
        OriginalConnectionPool = psycopg_pool.ConnectionPool

        # Define the correct connection string for the CI service container.
        ci_conninfo = "postgresql://postgres:postgres@postgres:5432/gradcafe"

        # Create our correctly configured, singleton pool for the entire test session.
        # `wait_pool` makes the connection resilient to small startup delays.
        ci_pool = OriginalConnectionPool(ci_conninfo, open=psycopg_pool.wait_pool)

        # Create a custom class to replace the original. Its __new__ method
        # will intercept any attempt by the application to create a new pool.
        class PatchedConnectionPool(OriginalConnectionPool):
            def __new__(cls, *args, **kwargs):
                # When any part of the app tries to instantiate ConnectionPool,
                # we ignore the arguments it provides (like the incorrect
                # 'localhost' URL) and return our pre-configured instance.
                return ci_pool

        # Patch the class in the psycopg_pool module. This is the crucial step.
        mp.setattr(psycopg_pool, "ConnectionPool", PatchedConnectionPool)

        yield  # Run all the tests

        # After all tests run, close the pool and undo the patch.
        ci_pool.close()
        mp.undo()
    else:
        # For local runs, we disable the database entirely to keep unit
        # tests fast and isolated.
        import psycopg_pool
        class NoopPool:
            def __init__(self, *a, **k): pass
            def connection(self): raise RuntimeError("ConnectionPool disabled in local tests.")
            def close(self): pass
        mp.setattr(psycopg_pool, "ConnectionPool", NoopPool)
        yield
        mp.undo()


# -------------------------------------------------------------------
# 2) Flask app & client
#    Import create_app lazily so it sees the patches.
# -------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    from app import create_app
    app_instance = create_app()
    app_instance.config["TESTING"] = True
    return app_instance


@pytest.fixture
def client(app):
    return app.test_client()


# -------------------------------------------------------------------
# 3) Global autouse stubs for routes.query_data.* functions.
# -------------------------------------------------------------------
@pytest.fixture(autouse=True)
def stub_queries(monkeypatch):
    import app.routes as routes

    def patch(name, value):
        if hasattr(routes.query_data, name):
            monkeypatch.setattr(routes.query_data, name, value)

    patch("count_fall_2025", lambda: 1)
    patch("percent_international", lambda: {
        "international_count": 1, "us_count": 1, "other_count": 0
    })
    patch("avg_scores", lambda: {
        "avg_gpa": 3.4, "avg_gre": 165, "avg_gre_v": 158, "avg_gre_aw": 4.5
    })
    patch("avg_gpa_american_fall2025", lambda: 3.2)
    patch("acceptance_rate_fall2025", lambda: 37.12)
    patch("avg_gpa_fall2025_acceptances", lambda: 3.6)
    patch("count_jhu_masters_cs", lambda: 7)
    patch("count_gt_phd_accept", lambda: 2)
    patch("degree_counts_2025", lambda: [("Masters", 10)])
    patch("top_5_programs", lambda: [("CS", 8)])


# -------------------------------------------------------------------
# 4) DB isolation fixture for tests that modify the database.
# -------------------------------------------------------------------
@pytest.fixture
def clean_db():
    if os.getenv("CI") != "true":
        pytest.skip("DB fixtures are only enabled in CI environment")

    import app.db as db
    db.ensure_table()
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()
    yield
    with db.pool.connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE applicants;")
        conn.commit()


# -------------------------------------------------------------------
# 5) Helper to make the data pipeline run synchronously in tests.
# -------------------------------------------------------------------
@pytest.fixture
def install_sync_pipeline(monkeypatch):
    def _install(rows):
        import app.routes as routes
        import app.db_helper as dbh

        def fake_insert_records_by_url(objs, _data_type):
            return len(objs)
        monkeypatch.setattr(dbh, "insert_records_by_url", fake_insert_records_by_url)

        def fake_run_pipeline(*_a, **_k):
            inserted = fake_insert_records_by_url(rows, None)
            return {
                "cleaned": len(rows), "llm": len(rows),
                "inserted": inserted, "message": "ok"
            }
        class FakeThread:
            def __init__(self, target, args=(), daemon=None):
                self._target, self._args = target, args
            def start(self):
                self._target(*self._args)

        monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)
        monkeypatch.setattr(routes.threading, "Thread", FakeThread)
        routes._pull_running.clear()

    return _install

