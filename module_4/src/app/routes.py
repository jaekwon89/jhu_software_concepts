from flask import (
    Blueprint, 
    render_template, 
    redirect, 
    url_for, 
    flash,
    jsonify,
    current_app
)

import threading

from . import query_data
from .pipeline import run_pipeline

# Blueprint for this module's routes.
bp = Blueprint("main", __name__)

# A process-wide flag indicating whether a pull is running.
# Using an Event is thread-safe and avoids overlapping runs.
_pull_running = threading.Event()


@bp.route("/")
def index():
    """Redirect root URL to the analysis page.

    :return: Redirect response to ``/analysis``.
    :rtype: werkzeug.wrappers.response.Response
    """
    return redirect(url_for("main.analysis"))

@bp.route("/analysis")
def analysis():
    """Render the analysis dashboard with precomputed metrics.

    Queries multiple metrics from the database via :mod:`query_data` and
    computes percentages for display.

    :return: Rendered HTML page with data injected.
    :rtype: str
    """
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
    data["q2_percent_international"] = (
        (c["international_count"] / total * 100) if total else 0.0
    )

    return render_template("analysis.html", data=data, term_label="Fall 2025")

@bp.route("/pull-data", methods=["POST"])
def pull_data():
    """Start a background pipeline run to fetch and insert new data.

    If a pull is already running, flashes a warning. Otherwise, starts a
    background thread that calls :func:`pipeline.run_pipeline` inside an
    application context.

    :return: Redirect back to the analysis page with a flash message.
    :rtype: werkzeug.wrappers.response.Response
    """
    if _pull_running.is_set():
        return jsonify({"busy": True}), 409


    def worker(app):
        """Run the pipeline inside an application context.

        :param app: The Flask application instance.
        :type app: flask.Flask
        """
        with app.app_context():
            try:
                _pull_running.set()
                # Tune max_records/delay as needed
                run_pipeline(max_records=100, delay=0.5)
                app.logger.info("Pipeline finished successfully.")
            except Exception as exc:
                app.logger.error(f"Pipeline failed: {exc}")
            finally:
                _pull_running.clear()

    # Capture the real Flask app for use in the thread.
    app = current_app._get_current_object()
    
    # Set the running flag before starting the thread to avoid races.
    _pull_running.set()
    threading.Thread(target=worker, args=(app,), daemon=True).start()
    
    flash("Pull Data started… scraping new rows and updating the database.", "info")
    return redirect(url_for("main.analysis"))

@bp.route("/update-analysis", methods=["POST"])
def update_analysis():
    """Refresh the analysis page once a pipeline run is finished.

    If a pull is still running, notifies the user to wait. Otherwise,
    reloads data from the database.

    :return: Redirect back to the analysis page with a flash message.
    :rtype: werkzeug.wrappers.response.Response
    """
    # Check if the background task is still running.
    if _pull_running.is_set():
        # If it is, tell the user to wait and try again.
        return jsonify({"busy": True}), 409
    else:
        # If it's finished, refresh the data as usual.
        flash("Analysis refreshed with the latest database results.", "success")
        return redirect(url_for("main.analysis"))