"""Flask routes and HTTP endpoints for the application UI and actions."""
import threading

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
)

from . import query_data
from .pipeline import run_pipeline

bp = Blueprint("main", __name__)

# Thread-safe flag to prevent overlapping runs.
_pull_running = threading.Event()


@bp.route("/")
def index():
    """Redirect root URL to the analysis page."""
    return redirect(url_for("main.analysis"))


@bp.route("/analysis")
def analysis():
    """Render the analysis dashboard with precomputed metrics."""
    data = {
        "q1_applicant_count": query_data.count_fall_2025(),
        "q2_counts": query_data.percent_international(),
        "q2_percent_international": None,
        "q3_avgs": query_data.avg_scores(),
        "q4_avg_gpa_us": query_data.avg_gpa_american_fall2025(),
        "q5_accept_rate": query_data.acceptance_rate_fall2025(),
        "q6_avg_gpa_accept": query_data.avg_gpa_fall2025_acceptances(),
        "q7_jhu_ms_cs": query_data.count_jhu_masters_cs(),
        "q8_georgetown_phd_cs": query_data.count_gt_phd_accept(),
        "q9_degree_counts": query_data.degree_counts_2025(),
        "q10_top_programs": query_data.top_5_programs(),
    }

    # Compute international %
    c = data["q2_counts"]
    total = c["international_count"] + c["us_count"] + c["other_count"]
    data["q2_percent_international"] = (c["international_count"] / total * 100) if total else 0.0

    return render_template("analysis.html", data=data, term_label="Fall 2025")


@bp.route("/pull-data", methods=["POST"])
def pull_data():
    """Kick off the background data pipeline if not already running."""
    if _pull_running.is_set():
        return jsonify({"busy": True}), 409

    # Capture the real Flask app for the background thread.
    app = current_app._get_current_object()  # pylint: disable=protected-access

    def worker(flask_app):
        """Run the pipeline inside an app context."""
        with flask_app.app_context():
            try:
                # Tune max_records/delay as needed
                run_pipeline(max_records=100, delay=0.5)
                flask_app.logger.info("Pipeline finished successfully.")
            except Exception:  # pylint: disable=broad-exception-caught  # pragma: no cover
                # Log full traceback without crashing the process.
                flask_app.logger.exception("Pipeline failed")
            finally:
                _pull_running.clear()

    # Set the flag before starting the thread to avoid races.
    _pull_running.set()
    threading.Thread(target=worker, args=(app,), daemon=True).start()

    flash("Pull Data started… scraping new rows and updating the database.", "info")
    return redirect(url_for("main.analysis"))


@bp.route("/update-analysis", methods=["POST"])
def update_analysis():
    """If pull is done, refresh the analysis; otherwise tell the client we're busy."""
    if _pull_running.is_set():
        return jsonify({"busy": True}), 409
    # Finished, refresh as usual.
    flash("Analysis refreshed with the latest database results.", "success")
    return redirect(url_for("main.analysis"))
