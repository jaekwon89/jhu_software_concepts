"""Unit tests for the app.query_data module.

This test file is specifically designed to test the data query functions
in isolation from the database and the global test configuration.

It achieves this by:
1.  Using a special fixture (`_reset_query_data`) to undo the global
    `conftest.py` stubs for this file only.
2.  Creating minimal, fake `psycopg_pool` objects (`_FakePool`,
    `_FakeConn`, `_FakeCursor`) that simulate the database connection
    and return pre-seeded data.
3.  Patching the `pool` object within `app.query_data` to use these
    fake objects, redirecting all SQL queries to our predefined data.
"""

import importlib  # stdlib first
import pytest     # third-party

from app import query_data as qd  # local imports
from app import routes


# -------------------------------------------------------------------
# Undo the conftest autouse stubs for this file so we call real funcs
# -------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_query_data(monkeypatch):
    """Override the global conftest stubbing for this test file.

    Reloads the `query_data` module to restore its functions and points
    `app.routes.query_data` back to the fresh module.
    """
    importlib.reload(qd)
    monkeypatch.setattr(routes, "query_data", qd)


# -------------------------------------------------------------------
# Tiny fake psycopg_pool objects with context-manager support
# -------------------------------------------------------------------
class _FakeCursor:
    """A fake database cursor that returns pre-seeded rows."""

    def __init__(self, rows):
        """Initialize with the list of rows to return."""
        self._rows = rows

    # allow: with conn.cursor() as cur:
    def __enter__(self):
        """Enter the runtime context for a `with` statement."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Exit the runtime context."""
        return False

    def execute(self, *_a, **_k):
        """Simulate executing a query; rows are pre-seeded per test."""
        return None  # no-op (avoid W0107)

    def fetchone(self):
        """Return the first pre-seeded row, or None if empty."""
        return self._rows[0] if self._rows else None

    def fetchall(self):
        """Return all pre-seeded rows."""
        return list(self._rows)

    def close(self):
        """Simulate closing the cursor."""
        return None  # no-op (avoid W0107)


class _FakeConn:
    """A fake database connection that yields a _FakeCursor."""

    def __init__(self, rows):
        """Initialize with the rows to be passed to the cursor."""
        self._rows = rows

    # allow: with pool.connection() as conn:
    def __enter__(self):
        """Enter the runtime context for a `with` statement."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Exit the runtime context."""
        return False

    def cursor(self):
        """Return a new fake cursor with the pre-seeded rows."""
        return _FakeCursor(self._rows)


class _FakePool:
    """Minimal stand-in for psycopg_pool.ConnectionPool used by query_data."""

    def __init__(self, rows):
        """Initialize with the rows to be passed to new connections."""
        self._rows = rows

    def connection(self):
        """Yield a new _FakeConn instance."""
        return _FakeConn(self._rows)


def _patch_pool(monkeypatch, rows):
    """Patch app.query_data.pool so query functions read these rows."""
    monkeypatch.setattr(qd, "pool", _FakePool(rows))


# -------------------------------------------------------------------
# Unit tests for each exported query function
# -------------------------------------------------------------------
@pytest.mark.db
def test_count_fall_2025(monkeypatch):
    """Test `count_fall_2025` returns the first element of the first row."""
    _patch_pool(monkeypatch, [(13,)])
    assert qd.count_fall_2025() == 13


@pytest.mark.db
def test_percent_international(monkeypatch):
    """Test `percent_international` correctly maps tuple to dictionary."""
    _patch_pool(monkeypatch, [(4, 5, 1)])
    out = qd.percent_international()
    assert out == {"international_count": 4, "us_count": 5, "other_count": 1}


@pytest.mark.db
def test_avg_scores(monkeypatch):
    """Test `avg_scores` correctly maps its result tuple to a dictionary."""
    _patch_pool(monkeypatch, [(3.4, 165.0, 158.0, 4.5)])
    out = qd.avg_scores()
    assert out["avg_gpa"] == 3.4
    assert out["avg_gre"] == 165.0
    assert out["avg_gre_v"] == 158.0
    assert out["avg_gre_aw"] == 4.5


@pytest.mark.db
def test_avg_gpa_american_fall2025(monkeypatch):
    """Test `avg_gpa_american_fall2025` returns the correct scalar value."""
    _patch_pool(monkeypatch, [(3.2,)])
    assert qd.avg_gpa_american_fall2025() == 3.2


@pytest.mark.db
def test_acceptance_rate_fall2025(monkeypatch):
    """Test `acceptance_rate_fall2025` returns the correct scalar value."""
    _patch_pool(monkeypatch, [(42.0,)])  # 42% as numeric
    rate = qd.acceptance_rate_fall2025()
    assert 41.99 < float(rate) < 42.01


@pytest.mark.db
def test_avg_gpa_fall2025_acceptances(monkeypatch):
    """Test `avg_gpa_fall2025_acceptances` returns the correct scalar value."""
    _patch_pool(monkeypatch, [(3.6,)])
    assert qd.avg_gpa_fall2025_acceptances() == 3.6


@pytest.mark.db
def test_count_jhu_masters_cs(monkeypatch):
    """Test `count_jhu_masters_cs` returns the correct scalar value."""
    _patch_pool(monkeypatch, [(7,)])
    assert qd.count_jhu_masters_cs() == 7


@pytest.mark.db
def test_count_gt_phd_accept(monkeypatch):
    """Test `count_gt_phd_accept` returns the correct scalar value."""
    _patch_pool(monkeypatch, [(2,)])
    assert qd.count_gt_phd_accept() == 2


@pytest.mark.db
def test_degree_counts_2025(monkeypatch):
    """Test `degree_counts_2025` returns the full list of rows."""
    rows = [("Masters", 10), ("PhD", 3)]
    _patch_pool(monkeypatch, rows)
    assert qd.degree_counts_2025() == rows


@pytest.mark.db
def test_top_5_programs(monkeypatch):
    """Test `top_5_programs` returns the full list of rows."""
    rows = [("CS", 8), ("DS", 5)]
    _patch_pool(monkeypatch, rows)
    assert qd.top_5_programs() == rows
