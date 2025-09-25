"""Unit tests for the routes module."""
import re
import pytest
import app.routes as routes


@pytest.fixture(autouse=True)
def _stub_queries(monkeypatch):
    """Stub all database query functions to return static, predictable data.

    This autouse fixture runs for every test, ensuring that route handlers
    are decoupled from the database query logic. This allows for fast,
    isolated unit tests of the routes without needing a database connection.
    It patches functions in the `query_data` module with lambdas that
    return fixed values.
    """

    def patch(name, value):
        """Helper to safely patch attributes on the query_data module."""
        assert hasattr(routes.query_data, name), f"query_data missing '{name}'"
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
    patch("acceptance_rate_fall2025", lambda: 37.12)  # ensure %.2f renders
    patch("avg_gpa_fall2025_acceptances", lambda: 3.6)
    patch("count_jhu_masters_cs", lambda: 7)
    patch("count_gt_phd_accept", lambda: 2)
    patch("degree_counts_2025", lambda: [("Masters", 10)])
    patch("top_5_programs", lambda: [("CS", 8)])


@pytest.mark.analysis
def test_includes_answer_labels(client):
    """Verify that the analysis page includes 'Answer:' labels for clarity.

    This test checks that the rendered HTML of the /analysis endpoint
    contains the specific string "Answer:", ignoring case, to ensure that
    key data points are clearly marked for the user.
    """
    r = client.get("/analysis")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert re.search(r"\bAnswer:", html, flags=re.IGNORECASE)


@pytest.mark.analysis
def test_percentages_have_two_decimals(client):
    """Verify that all percentages on the analysis page are formatted to two decimal places.

    This test uses a regular expression to scan the HTML of the /analysis
    endpoint. It asserts that any number followed by a percent sign (%)
    is formatted with exactly two digits after the decimal point,
    ensuring consistent and professional presentation of data.
    """
    r = client.get("/analysis")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert re.search(r"\b\d{1,3}\.\d{2}\s*%", html), (
        "Expect percent with two decimals like 16.67%"
    )