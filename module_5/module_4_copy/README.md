# Module 4: Pytest and Sphinx

## Overview
This module turns the GradCafe Analyzer into a tested, documented, CI-backed service. It involves (1) building a Pytest suite for the Flask web and ETL/DB layers, (2) achieving 100% coverage, and (3) publishing developer docs with Sphinx on Read the Docs. The goal is a stable, extensible system that other developers can run, test, and extend.

## Sphinx Documentation on Read the Doc
Address: https://jhu-software-conceptsmodule-4.readthedocs.io/en/latest/

## Project Structure
```text
jhu_software_concepts/             # GitHub repo
├─  ...
├─ .github/workflows/              # Contains the CI pipeline configuration
│    └── test.yml
└─ module_4/
     ├── docs/                     # Sphinx documentation source files
     ├── src/                      # All application source code
     │   ├── app/                  # The core Flask application package
     │   └── ...
     ├── tests/                    # All pytest test files
     │   ├─ conftest.py
     │   ├─ test_web.py            # -m web
     │   ├─ test_buttons.py        # -m buttons
     │   ├─ test_analysis.py       # -m analysis
     │   ├─ test_db.py             # -m db
     │   ├─ test_integration.py    # -m integration
     │   └─ ...                    # Other test files
     │  
     ├── .coveragerc               # Configuration for test coverage reporting
     ├── coverage._summary.txt     # Saved terminal coverage summary
     ├── pytest.ini                # Configuration for pytest, including markers
     ├── requirements.txt          # Runtime/dev deps
     ├── Screenshots_CI.docx       # GA “green” run screenshot
     ├── README.md                 # This file
     │ 
     └── .github_copy/workflows/   # A copy of .github/workflows/test.yml for submission
        └── test_copy.yml
```

## Features
- **Testing**: 
  1. Flask App & Page Rendering
  2. Buttons & Busy_state Behavior
  3. Analysis formatting (two-decimal percentages)
  4. DB writes/uniqueness
  5. Integration Tests (End-to-end flows)
- **Coverage**: Enforced to 100% with `pytest` (summary saved to `coverage_summary.txt`).
- **Docs**: Sphinx site (overview/setup, architecture, testing guide, API autodoc) hosted on Read the Docs.
- **CI**: Automated testing pipeline using GitHub Actions that runs on every push and pull request.

### LLM-generated artifacts
- Unit tests
- HTML templates
- YAML config files (`.yml`/`.yaml`)
- Sphinx-style Python docstrings

## Test Coverage Summary
```text
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
src\__init__.py             0      0   100%
src\app\__init__.py         9      0   100%
src\app\db.py               9      0   100%
src\app\db_helper.py       42      0   100%
src\app\pipeline.py        29      0   100%
src\app\query_data.py      63      0   100%
src\app\routes.py          38      0   100%
-----------------------------------------------------
TOTAL                     190      0   100%
```