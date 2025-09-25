"""Sphinx configuration for GradCafe Analyzer docs.

Notes for linters:
- Sphinx expects many lowercase module-level config variables
  (e.g., `project`, `html_theme`). We disable `invalid-name`
  for this file to avoid fighting Pylint over that convention.
"""
# pylint: disable=invalid-name

from pathlib import Path
import sys

# ---- Path setup: add <repo>/src so autodoc can import `src.app...`
DOCS_DIR = Path(__file__).resolve().parent            # module_4_copy/docs/source
PROJECT_ROOT = DOCS_DIR.parents[1]                    # -> module_4_copy
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

# ---- Project information
project = "GradCafe Analyzer"
author = "Jae Kwon"
COPYTRIGHT = "2025, Jae Kwon"
release = "0.1.0"

# ---- General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]
autosummary_generate = True

# Mock heavy/optional deps so autodoc import succeeds without them installed
autodoc_mock_imports = ["psycopg_pool", "psycopg", "psycopg2", "urllib3", "bs4"]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": False,
    "show-inheritance": True,
}

templates_path = ["_templates"]
exclude_patterns = []

# ---- HTML output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
