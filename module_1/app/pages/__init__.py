# module_1/app/pages/__init__.py
from flask import Blueprint

pages_bp = Blueprint("pages", __name__)

from . import views