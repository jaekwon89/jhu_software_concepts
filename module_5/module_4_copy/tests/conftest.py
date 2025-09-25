# pylint: disable=missing-function-docstring
"""Global configuration and fixtures for the pytest test suite.

<snip of your docstring unchanged>
"""

# Tests intentionally import inside functions/fixtures to control timing and
# avoid heavy imports. Silence that globally.
# pylint: disable=import-outside-toplevel

import os
import importlib
from types import SimpleNamespace
import pytest


# -------------------------------------------------------------------
# 1) Conditionally configure the database for the test session.
# -------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _setup_db_for_session():
    """Configure the database connection for the entire test session.

    - In CI ("CI" == "true"), reload db modules so they pick up CI env vars.
    - Locally, replace psycopg_pool.ConnectionPool with a NoopPool that
      prevents DB access, keeping tests fast and isolated.
    """
    mp = pytest.MonkeyPatch()

    if os.getenv("CI") == "true":
        if "app.db" in importlib.sys.modules:
            importlib.reload(importlib.sys.modules["app.db"])
        if "app.query_data" in importlib.sys.modules:
            importlib.reload(importlib.sys.modules["app.query_data"])
        yield
    else:
        # Import psycopg_pool if available; otherwise create a stub namespace
        try:
            import psycopg_pool  # pylint: disable=import-error
        except ImportError:
            import sys
            psycopg_pool = SimpleNamespace()  # type: ignore
            sys.modules["psycopg_pool"] = psycopg_pool

        class NoopPool:
            """A dummy connection pool that prevents any actual DB connections."""

            def __init__(self, *_args, **_kwargs):
                """Initialize (no-op)."""

            def connection(self):
                """Always fail: DB disabled in local tests."""
                raise RuntimeError("ConnectionPool disabled in local tests.")

            def close(self):
                """Close (no-op)."""

        mp.setattr(psycopg_pool, "ConnectionPool", NoopPool)
        yield
        mp.undo()


# -------------------------------------------------------------------
# 2) Flask app & client
# -------------------------------------------------------------------
@pytest.fixture(name="app", scope="session")
def flask_app():
    """Create and configure a new app instance for the test session."""
    from app import create_app

    app_instance = create_app()
    app_instance.config["TESTING"] = True
    return app_instance


@pytest.fixture
def client(app):
    """Provide a test client for the Flask app."""
    return app.test_client()


# -------------------------------------------------------------------
# 3) Global autouse stubs for routes.query_data.* functions.
# -------------------------------------------------------------------
@pytest.fixture(autouse=True)
def stub_queries(monkeypatch):
    """Stub database query functions to return static, predictable data."""
    import app.routes as routes

    def patch(name, value):
        if hasattr(routes.query_data, name):
            monkeypatch.setattr(routes.query_data, name, value)

    patch("count_fall_2025", lambda: 1)
    patch(
        "percent_international",
        lambda: {"international_count": 1, "us_count": 1, "other_count": 0},
    )
    patch(
        "avg_scores",
        lambda: {"avg_gpa": 3.4, "avg_gre": 165, "avg_gre_v": 158, "avg_gre_aw": 4.5},
    )
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
    """Ensure the database is clean for tests that perform writes (CI only)."""
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
    """Provide a helper to make the async data pipeline run synchronously."""

    def _install(rows):
        """Patch the app to run the data pipeline synchronously with fake data."""
        import app.routes as routes
        import app.db_helper as dbh

        def fake_insert_records_by_url(objs, _data_type):
            """Fake the database insertion step."""
            return len(objs)

        monkeypatch.setattr(dbh, "insert_records_by_url", fake_insert_records_by_url)

        def fake_run_pipeline(*_args, **_kwargs):
            """Run a simplified, synchronous version of the pipeline."""
            inserted = fake_insert_records_by_url(rows, None)
            return {
                "cleaned": len(rows),
                "llm": len(rows),
                "inserted": inserted,
                "message": "ok",
            }

        class FakeThread:
            """A fake Thread that executes its target immediately."""

            def __init__(self, target, args=(), daemon=None):
                self._target, self._args = target, args
                self._daemon = daemon  # mark used: avoid W0613

            def start(self):
                self._target(*self._args)

        monkeypatch.setattr(routes, "run_pipeline", fake_run_pipeline)
        monkeypatch.setattr(routes.threading, "Thread", FakeThread)
        routes._pull_running.clear()  # pylint: disable=protected-access

    return _install
