from flask import Blueprint, render_template, redirect, url_for
from . import query_data

bp = Blueprint("main", __name__)

@bp.route("/")
def index():

    return redirect(url_for("main.analysis"))

@bp.route("/analysis")
def analysis():
    data = {
        "q1_applicant_count": query_data.count_fall_2025(),
        "q2_counts": query_data.percent_international(),
        "q2_percent_international": None,
        "q3_avgs": query_data.avg_scores(),
        "q4_avg_gpa_us": query_data.avg_gpa_american_fall2025(),
        "q5_accept_rate": query_data.acceptance_rate_fall2025(),
        "q6_avg_gpa_accept": query_data.avg_gpa_fall2025_acceptances(),
        "q7_jhu_ms_cs": query_data.count_jhu_masters_cs(),
        "q8_georgetown_phd_cs": query_data.count_gt_phd_aceept(),
        "q9_degree_counts": query_data.degree_counts_2025(),
        "q10_top_programs": query_data.top_5_programs(),
    }

    # Compute international %
    c = data["q2_counts"]
    total = c["international_count"] + c["us_count"] + c["other_count"]
    data["q2_percent_international"] = (
        (c["international_count"] / total * 100) if total else 0.0
    )

    return render_template("analysis.html", data=data, term_label="Fall 2025")