from flask import Blueprint, render_template, redirect, url_for, flash, current_app
import threading
from . import query_data
from .pipeline import run_pipeline

bp = Blueprint("main", __name__)
_pull_running = threading.Event()

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

@bp.route("/pull-data", methods=["POST"])
def pull_data():
    if _pull_running.is_set():
        flash("A data pull is already running. Please wait.", "warning")
        return redirect(url_for("main.analysis"))

    # 1. Define the worker to accept the 'app' object as an argument.
    def worker(app):
        # 2. Use the passed-in 'app' to create the context and log messages.
        with app.app_context():
            try:
                run_pipeline(max_records=200, delay=0.5)
                app.logger.info("Pipeline finished successfully.")
            except Exception as exc:
                app.logger.error(f"Pipeline failed: {exc}")
            finally:
                _pull_running.clear()

    # 3. Get a direct reference to the current application object.
    app = current_app._get_current_object()
    
    _pull_running.set()
    # 4. Pass the 'app' object to the thread using the 'args' parameter.
    #    Note the comma in '(app,)' which makes it a tuple.
    threading.Thread(target=worker, args=(app,), daemon=True).start()
    
    flash("Pull Data started… scraping new rows and updating the database.", "info")
    return redirect(url_for("main.analysis"))

@bp.route("/update-analysis", methods=["POST"])
def update_analysis():
    # Check if the background task is still running
    if _pull_running.is_set():
        # If it is, tell the user to wait and try again
        flash("Data pull is still running. Please wait a moment and try again.", "warning")
    else:
        # If it's finished, refresh the data as usual
        flash("Analysis refreshed with the latest database results.", "success")
        
    return redirect(url_for("main.analysis"))