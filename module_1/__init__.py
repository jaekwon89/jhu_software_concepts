# module_1/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # register blueprints
    from .pages import pages_bp
    app.register_blueprint(pages_bp)

    with app.app_context():
        print(app.url_map)


    return app