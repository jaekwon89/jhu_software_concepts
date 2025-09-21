# Module 4: Pytest and Sphinx

## Overview
This module turns the GradCafe Analyzer into a tested, documented, CI-backed service. It involves (1) building a Pytest suite for the Flask web and ETL/DB layers, (2) achieving 100% coverage, and (3) publishing developer docs with Sphinx on Read the Docs. The goal is a stable, extensible system that other developers can run, test, and extend.

```text
jhu_software_concepts/                 # GitHub repo (monorepo)
├─ module_1/
├─ module_2/
├─ module_3/
├─ module_4/                           # <-- current assignment
│  ├─ src/                             # application code (import as `src.*`)
│  │  ├─ app/
│  │  │  ├─ __init__.py
│  │  │  ├─ routes.py
│  │  │  └─ ...
│  │  ├─ db.py
│  │  ├─ query_data.py
│  │  └─ ...
│  ├─ tests/                           # pytest suite (all tests are marked)
│  │  ├─ conftest.py
│  │  ├─ test_web.py                   # -m web
│  │  ├─ test_buttons.py               # -m buttons
│  │  ├─ test_analysis.py              # -m analysis
│  │  ├─ test_db.py                    # -m db
│  │  └─ test_integration.py           # -m integration
│  ├─ docs/                            # Sphinx documentation
│  │  ├─ source/
│  │  │  ├─ conf.py                    # adds parent of `src` to sys.path; enables autodoc/myst
│  │  │  ├─ index.rst                  # toctree root
│  │  │  ├─ api/                       # autodoc stubs (sphinx-apidoc output)
│  │  │  │  ├─ modules.rst
│  │  │  │  └─ src.app.rst
│  │  │  ├─ guides/                    # prose pages (overview, testing, arch)
│  │  │  │  ├─ overview.md
│  │  │  │  ├─ testing.md
│  │  │  │  └─ architecture.md
│  │  │  └─ _static/                   # custom CSS/images (optional)
│  │  └─ build/                        # local HTML output (gitignored)
│  ├─ .readthedocs.yaml                # points to docs/source/conf.py
│  ├─ requirements.txt                 # runtime/dev deps for module_4
│  ├─ README.md                        # module-specific readme
│  ├─ coverage_summary.txt             # saved terminal coverage summary
│  └─ actions_success.png              # GA “green” run screenshot
├─ .github/
│  └─ workflows/
│     └─ tests.yml                     # CI: starts Postgres, runs pytest
├─ pytest.ini                          # addopts, markers, paths
├─ .gitignore
└─ README.md                           # repo root overview (links to modules & docs)
```