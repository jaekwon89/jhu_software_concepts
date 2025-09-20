import pytest
import os

# -------------------------------------------------------------------
# 1) Conditionally configure the database for the test session.
# -------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _setup_db_for_session():
    # We must use a manually instantiated MonkeyPatch for session-scoped fixtures.
    mp = pytest.MonkeyPatch()

    if os.getenv("CI") == "true":
        # In the CI environment, we need a real database connection.
        # The app's default pool is created at module import time and may be
        # misconfigured for localhost. We must replace it with a pool that
        # correctly points to the 'postgres' service container.
        import app.db
        import psycopg_pool

        # Define the correct connection string for the CI service container.
        ci_conninfo = "postgresql://postgres:postgres@postgres:5432/gradcafe"

        # Create a new pool with the correct settings. Using `wait_pool` makes
        # the connection resilient to small delays in the service starting up.
        ci_pool = psycopg_pool.ConnectionPool(ci_conninfo, open=psycopg_pool.wait_pool)

        # Atomically replace the old, misconfigured pool with our new one.
        mp.setattr(app.db, 'pool', ci_pool)
        
        yield
        
        # After all tests run, close the pool and undo the patch.
        ci_pool.close()
        mp.undo()
    else:
        # For local runs, we disable the database by default to keep unit
        # tests fast and isolated. We patch the entire ConnectionPool class.
        import psycopg_pool
        class NoopPool:
            def __init__(self, *a, **k): pass
            def connection(self): raise RuntimeError("ConnectionPool disabled in local tests. Use a DB-specific mark to enable.")
            def close(self): pass
        mp.setattr(psycopg_pool, "ConnectionPool", NoopPool)
        yield
        mp.undo()


# -------------------------------------------------------------------
# 2) Flask app & client
#    Import create_app lazily so it sees the environment variable/patches.
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
# 3) Global autouse stubs for routes.query_data.* so /analysis never
#    rounds None. Import routes lazily (after patch).
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
# 4) DB isolation when a test needs the real applicants table.
#    Import db lazily (after patch); opt-in per test.
# -------------------------------------------------------------------
@pytest.fixture
def clean_db():
    # This fixture will only work in CI now, as the pool is disabled locally.
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
# 5) Helper to run /pull-data synchronously in tests.
#    Import lazily; clears busy flag.
# -------------------------------------------------------------------
@pytest.fixture
def install_sync_pipeline(monkeypatch):
    """
    Make /pull-data run synchronously without touching a real DB:

      - routes.run_pipeline -> fake that returns counts
      - app.db_helper.insert_records_by_url -> fake that just counts rows
      - threading.Thread -> FakeThread that runs immediately
      - clear the busy flag
    """
    def _install(rows):
        import app.routes as routes
        import app.db_helper as dbh  # patch function here

        # DB-free insert: just count unique URLs (or all rows; either is fine for tests)
        def fake_insert_records_by_url(objs, _data_type):
            return len(objs)

        monkeypatch.setattr(dbh, "insert_records_by_url", fake_insert_records_by_url)

        def fake_run_pipeline(*_a, **_k):
            inserted = fake_insert_records_by_url(rows, None)
            return {
                "cleaned": len(rows),
                "llm": len(rows),
                "inserted": inserted,
                "message": "ok",
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

