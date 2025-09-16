from flask import Flask
from .db import ensure_table

# Create and configure the Flask application.
def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "dev-only-change-me"
    
    # Ensure DB schema exists before routes use it.
    ensure_table()

    # Local import to avoid potential circular imports.
    from .routes import bp
    app.register_blueprint(bp)

    return app
