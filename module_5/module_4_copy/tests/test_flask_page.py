"""Tests for the Flask application setup, routes, and page rendering.

This module contains tests to verify:
- The Flask application factory correctly registers all expected endpoints.
- The main pages (`/` and `/analysis`) render successfully with the
  required components, such as titles and buttons.
- Stubs are used for all database queries to ensure that rendering logic
  can be tested in isolation without a live database connection.
"""

import re
import pytest
from bs4 import BeautifulSoup

import app.routes as routes


# Stub data to avoid None -> round() errors during page render
@pytest.fixture(autouse=True)
def _stub_queries(monkeypatch):
    """Stub all database query functions to return static, predictable data.

    This autouse fixture runs for every test in this module. It ensures that
    when pages are rendered, the route handlers that call database query
    functions receive predictable, non-None values. This prevents errors
    during template rendering and allows for isolated testing of the web UI.
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
    patch("acceptance_rate_fall2025", lambda: 37.12)
    patch("avg_gpa_fall2025_acceptances", lambda: 3.6)
    patch("count_jhu_masters_cs", lambda: 7)
    patch("count_gt_phd_accept", lambda: 2)
    patch("degree_counts_2025", lambda: [("Masters", 10)])
    patch("top_5_programs", lambda: [("CS", 8)])


# Test App factory - checking expected endpoints
@pytest.mark.web
def test_routes(app):
    """Verify that the Flask app factory registers all expected endpoints.

    This test inspects the application's registered view functions to ensure
    that all critical routes for the web interface are present.
    """
    endpoints = set(app.view_functions.keys())
    assert "main.index" in endpoints  # "/"
    assert "main.analysis" in endpoints  # "/analysis"
    assert "main.pull_data" in endpoints  # "/pull-data" (POST)
    assert "main.update_analysis" in endpoints  # "/update-analysis" (POST)


# Test GET /analysis (page load)
@pytest.mark.web
def test_analysis_page(client):
    """Ensure GET /analysis renders the page with required text and buttons.

    This test performs a GET request to the /analysis endpoint and checks for:
    - A successful 200 OK status code.
    - The presence of "Pull Data" and "Update Analysis" buttons.
    - The inclusion of the word "Analysis" and at least one "Answer:" label
      in the page content, confirming the template is rendered correctly.
    """
    # Request the page: status 200
    r = client.get("/analysis")
    assert r.status_code == 200

    # Parse HTML
    soup = BeautifulSoup(r.data.decode(), "html.parser")

    # Two buttons present
    assert soup.find("button", string=re.compile(r"^\s*Pull Data\s*$", re.I))
    assert soup.find("button", string=re.compile(r"^\s*Update Analysis\s*$", re.I))

    # Includeds "Analysis" and at least one "Answer:" (case-insensitive)
    assert soup.find(string=re.compile(r"Analysis", re.I))
    assert soup.find(string=re.compile(r"\bAnswer:", re.I))