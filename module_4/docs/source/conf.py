# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "GradCafe Analyzer"
copyright = "2025, Jae Kwon"
author = "Jae Kwon"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os, sys

# from docs/source -> ../../src  (so Python can import "app.*")
DOCS_DIR = os.path.abspath(os.path.dirname(__file__))          # module_4/docs/source
PROJECT_ROOT = os.path.abspath(os.path.join(DOCS_DIR, "..", ".."))  # -> module_4
sys.path.insert(0, PROJECT_ROOT)

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",  # Google/Numpy style, also fine with your reST fields
    "sphinx.ext.viewcode",
    "myst_parser",  # you’re already using this
]
autosummary_generate = True

# mock heavy or optional deps so autodoc can import modules safely
autodoc_mock_imports = ["psycopg_pool", "psycopg", "psycopg2", "urllib3", "bs4"]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": False,
    "show-inheritance": True,
}

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
