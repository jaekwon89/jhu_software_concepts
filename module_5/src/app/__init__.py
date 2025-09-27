"""Flask application factory.

This module provides a ``create_app`` function that:

* Creates and configures a Flask application.
* Ensures the database schema exists.
* Registers the main blueprint (:mod:`routes`).

Usage
-----

.. code-block:: python

   from app import create_app

   app = create_app()
   app.run()
"""

from flask import Flask
from .db import ensure_table


def create_app():
    """Create and configure the Flask application.

    - Sets a development secret key.
    - Ensures the database schema exists.
    - Registers the main blueprint.

    :return: A configured Flask application instance.
    :rtype: flask.Flask
    """
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev-only-change-me"

    ensure_table()

    from .routes import bp

    app.register_blueprint(bp)

    return app