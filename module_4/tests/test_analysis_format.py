import re
import pytest
import app.routes as routes

@pytest.fixture(autouse=True)
def _stub_queries(monkeypatch):
    def patch(name, value):
        assert hasattr(routes.query_data, name), f"query_data missing '{name}'"
        monkeypatch.setattr(routes.query_data, name, value)
    patch("count_fall_2025", lambda: 1)
    patch("percent_international", lambda: {"international_count": 1, "us_count": 1, "other_count": 0})
    patch("avg_scores", lambda: {"avg_gpa": 3.4, "avg_gre": 165, "avg_gre_v": 158, "avg_gre_aw": 4.5})
    patch("avg_gpa_american_fall2025", lambda: 3.2)
    patch("acceptance_rate_fall2025", lambda: 37.12)  # ensure %.2f renders
    patch("avg_gpa_fall2025_acceptances", lambda: 3.6)
    patch("count_jhu_masters_cs", lambda: 7)
    patch("count_gt_phd_accept", lambda: 2)
    patch("degree_counts_2025", lambda: [("Masters", 10)])
    patch("top_5_programs", lambda: [("CS", 8)])

@pytest.mark.analysis
def test_includes_answer_labels(client):
    r = client.get("/analysis")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert re.search(r"\bAnswer:", html, flags=re.IGNORECASE)

@pytest.mark.analysis
def test_percentages_have_two_decimals(client):
    r = client.get("/analysis")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert re.search(r"\b\d{1,3}\.\d{2}\s*%", html), "Expect percent with two decimals like 16.67%"

