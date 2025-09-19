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

# Create and configure the Flask application.
def create_app():
    """Create and configure the Flask application.

    - Sets a development secret key.
    - Ensures the database schema exists.
    - Registers the main blueprint.

    :return: A configured Flask application instance.
    :rtype: flask.Flask
    """
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "dev-only-change-me"
    
    # Ensure DB schema exists before routes use it.
    ensure_table()

    # Local import to avoid potential circular imports.
    from .routes import bp
    app.register_blueprint(bp)

    return app
