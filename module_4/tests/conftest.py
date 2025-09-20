import pytest
import os
import importlib

# -------------------------------------------------------------------
# 1) Conditionally configure the database for the test session.
# -------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _setup_db_for_session():
    # We use a manually instantiated MonkeyPatch for session-scoped fixtures
    # to avoid a "ScopeMismatch" error with the function-scoped `monkeypatch`.
    mp = pytest.MonkeyPatch()

    if os.getenv("CI") == "true":
        # In the CI environment, we MUST force the application to connect to the
        # 'postgres' service container instead of 'localhost'. We do this by
        # setting environment variables *before* the app's db modules are loaded.

        # Set environment variables for the database connection.
        mp.setenv("PGHOST", "postgres")
        mp.setenv("PGDATABASE", "gradcafe")
        mp.setenv("PGUSER", "postgres")
        mp.setenv("PGPASSWORD", "postgres")

        # --- CRUCIAL STEP ---
        # The application's db modules might have been imported and cached by
        # pytest before this fixture ran. We must force a reload to ensure they
        # pick up the new environment variables.
        if "app.db" in importlib.sys.modules:
            importlib.reload(importlib.sys.modules["app.db"])
        if "app.query_data" in importlib.sys.modules:
            importlib.reload(importlib.sys.modules["app.query_data"])

        yield  # Run all the tests

        mp.undo()  # Clean up the environment variables
    else:
        # For local runs, we disable the database entirely.
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
# -------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    # Now, when create_app is called, the reloaded db modules will be used.
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

