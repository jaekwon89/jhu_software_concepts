from flask import Flask
from .db import ensure_table

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "c8338bf3561f5fd6159fd22c546400ab0a302fb4fff02df1"
    
    ensure_table()

    from .routes import bp
    app.register_blueprint(bp)

    return app
