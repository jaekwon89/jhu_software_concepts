# Module 4: Pytest and Sphinx

## Overview
This module turns the GradCafe Analyzer into a tested, documented, CI-backed service. It involves (1) building a Pytest suite for the Flask web and ETL/DB layers, (2) achieving 100% coverage, and (3) publishing developer docs with Sphinx on Read the Docs. The goal is a stable, extensible system that other developers can run, test, and extend.

## Sphinx Documentation on Read the Doc
[Read the Docs site](https://jhu-software-conceptsmodule-4.readthedocs.io/en/latest/)

## Project Structure (Minimized)
```text
jhu_software_concepts/              # GitHub repo
├─  ...
├─ .github/workflows/               # Contains the CI pipeline configuration
│    └── test.yml
└─ module_4/
     ├── docs/                     # Sphinx documentation source files
     ├── src/                      # All application source code
     │   ├── app/                  # The core Flask application package
     │   └── ...
     ├── tests/                    # All pytest test files
     │   └── ...
     ├── .coveragerc               # Configuration for test coverage reporting
     ├── coverage._summary.txt     # Saved terminal coverage summary
     ├── pytest.ini                # Configuration for pytest, including markers
     ├── requirements.txt          # Runtime/dev deps for module_4
     ├── Screenshots_CI.docx       # GA “green” run screenshot
     └── README.md                 # This file
```