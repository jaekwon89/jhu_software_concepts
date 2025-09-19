import pytest
import importlib
import app.query_data as qd
import app.routes as routes

# -------------------------------------------------------------------
# Undo the conftest autouse stubs for this file so we call real funcs
# -------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_query_data(monkeypatch):
    # Reload the module to restore its actual function definitions
    importlib.reload(qd)
    # Point routes.query_data back to the freshly reloaded module
    monkeypatch.setattr(routes, "query_data", qd)

# -------------------------------------------------------------------
# Tiny fake psycopg_pool objects with context-manager support
# -------------------------------------------------------------------
class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    # allow: with conn.cursor() as cur:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *_a, **_k):
        # SQL not parsed in unit tests—rows are pre-seeded per test
        pass

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class _FakeConn:
    def __init__(self, rows):
        self._rows = rows

    # allow: with pool.connection() as conn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return _FakeCursor(self._rows)


class _FakePool:
    """Minimal stand-in for psycopg_pool.ConnectionPool used by query_data."""
    def __init__(self, rows):
        self._rows = rows

    def connection(self):
        return _FakeConn(self._rows)


def _patch_pool(monkeypatch, rows):
    """Patch app.query_data.pool so query functions read these rows."""
    monkeypatch.setattr(qd, "pool", _FakePool(rows))


# -------------------------------------------------------------------
# Unit tests for each exported query function
# -------------------------------------------------------------------
@pytest.mark.db
def test_count_fall_2025(monkeypatch):
    _patch_pool(monkeypatch, [(13,)])
    assert qd.count_fall_2025() == 13


@pytest.mark.db
def test_percent_international(monkeypatch):
    # function expects a single row: (international_count, us_count, other_count)
    _patch_pool(monkeypatch, [(4, 5, 1)])
    out = qd.percent_international()
    assert out == {"international_count": 4, "us_count": 5, "other_count": 1}


@pytest.mark.db
def test_avg_scores(monkeypatch):
    # function expects one row: (avg_gpa, avg_gre, avg_gre_v, avg_gre_aw)
    _patch_pool(monkeypatch, [(3.4, 165.0, 158.0, 4.5)])
    out = qd.avg_scores()
    assert out["avg_gpa"] == 3.4
    assert out["avg_gre"] == 165.0
    assert out["avg_gre_v"] == 158.0
    assert out["avg_gre_aw"] == 4.5


@pytest.mark.db
def test_avg_gpa_american_fall2025(monkeypatch):
    _patch_pool(monkeypatch, [(3.2,)])
    assert qd.avg_gpa_american_fall2025() == 3.2


@pytest.mark.db
def test_acceptance_rate_fall2025(monkeypatch):
    _patch_pool(monkeypatch, [(42.0,)])  # 42% as numeric
    rate = qd.acceptance_rate_fall2025()
    assert 41.99 < float(rate) < 42.01


@pytest.mark.db
def test_avg_gpa_fall2025_acceptances(monkeypatch):
    _patch_pool(monkeypatch, [(3.6,)])
    assert qd.avg_gpa_fall2025_acceptances() == 3.6


@pytest.mark.db
def test_count_jhu_masters_cs(monkeypatch):
    _patch_pool(monkeypatch, [(7,)])
    assert qd.count_jhu_masters_cs() == 7


@pytest.mark.db
def test_count_gt_phd_accept(monkeypatch):
    _patch_pool(monkeypatch, [(2,)])
    assert qd.count_gt_phd_accept() == 2


@pytest.mark.db
def test_degree_counts_2025(monkeypatch):
    rows = [("Masters", 10), ("PhD", 3)]
    _patch_pool(monkeypatch, rows)
    assert qd.degree_counts_2025() == rows


@pytest.mark.db
def test_top_5_programs(monkeypatch):
    rows = [("CS", 8), ("DS", 5)]
    _patch_pool(monkeypatch, rows)
    assert qd.top_5_programs() == rows
