# module_1/app/pages/views.py
from flask import render_template
from . import pages_bp

@pages_bp.route("/")
def home():
    return render_template("index.html", active_page="home")

@pages_bp.route("/projects")
def projects():
    return render_template("projects.html", active_page="projects")

@pages_bp.route("/contact")
def contact():
    return render_template("contact.html", active_page="contact")