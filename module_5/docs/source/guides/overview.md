# Overview & Setup

This project provides a Flask web app and ETL/DB pipeline for GradCafe data.

## Environment
- `PG_DSN` – e.g. `postgresql://postgres:postgres@127.0.0.1:5432/gradcafe`

## Run the app
```bash
cd module_4
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
flask --app src.app run --debug