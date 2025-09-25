"""Flask application factory.

This module provides a ``create_app`` function that:

* Creates and configures a Flask application.
* Ensures the database schema exists (when DB is available).
* Registers the main blueprint (:mod:`routes`).
"""

from flask import Flask
from .db import ensure_table
from .routes import bp  # import at module level to satisfy pylint C0415


def create_app() -> Flask:
    """Create and configure the Flask application.

    - Sets a development secret key.
    - Ensures the database schema exists (if DB is available).
    - Registers the main blueprint.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-change-me"

    # Ensure DB schema exists before routes use it.
    # In local tests, conftest replaces ConnectionPool with NoopPool that raises RuntimeError.
    try:
        ensure_table()
    except RuntimeError:
        # DB intentionally disabled (e.g., local tests). Proceed without ensuring schema.
        app.logger.info("Database unavailable; skipped ensure_table() during startup.")

    app.register_blueprint(bp)
    return app
