# Flask App & Page Rendering

import pytest
import re
from bs4 import BeautifulSoup


# Test App
@pytest.mark.web
def test_routes(app):
    """App factory creates an app that exposes expected endpoints."""
    endpoints = set(app.view_functions.keys())
    # Route "/": index()
    assert "main.index" in endpoints
    # Route "/analysis": analysis()
    assert "main.analysis" in endpoints


# Test GET /analysis (page load)
@pytest.mark.web
def test_analysis_page(app, client):
    # Request the page
    r = client.get("/analysis")
    assert r.status_code == 200

    # Parse HTML
    soup = BeautifulSoup(r.data.decode(), "html.parser")

    # Two buttons present
    assert soup.find(
        "button", 
        string=re.compile(r"^\s*Pull Data\s*$", re.I)
    )
    assert soup.find(
        "button", 
        string=re.compile(r"^\s*Update Analysis\s*$", re.I)
    )

    # Includeds "Analysis" and at least one "Answer:" (case-insensitive)
    assert soup.find(string=re.compile(r"Analysis", re.I))
    assert soup.find(string=re.compile(r"\bAnswer:", re.I))