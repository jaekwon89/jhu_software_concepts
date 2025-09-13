from flask import Flask
from .db import ensure_table

def create_app():
    app = Flask(__name__)
    ensure_table()

    from .routes import bp
    app.register_blueprint(bp)

    return app
