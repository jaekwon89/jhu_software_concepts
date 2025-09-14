Name: Jae Kwon (jkwon30)


Module Info: JHU EP 605.256 Module 3: SQL Data Analysis


Approach:
Blueprint: 
module_3/
|--- __init__.py              # Make module_3 a package
|--- run.py                   # Main entry point (runs web server or pipeline)
|--- load_data.py             # Load data to Postgres (30k data from module_2)
|--- query_data.py            # Functions for all SQL database queries to print output
|
|--- app/
    |--- __init__.py          # Create app
    |--- routes.py            # Defines all web routes and request handlers
    |--- db.py                # Database connection pool and table schema
    |--- db_helper.py         # DB helpers (insert_records_by_url)
    |--- pipeline.py          # Main pipeline orchestrator (scrape -> clean -> LLM -> load)
    |--- scrape.py            # Fetches raw data from the web (new data); code from module_2
    |--- clean.py             # Cleans raw data (status, dates); code from module_2
    |--- query_data.py        # Functions for all SQL database queries for website
    |
    |--- llm_hosting/
    |   |--- app.py           # Runs the LLM-based data normalization
    |
    |--- static/              # For CSS and other static assets
    |--- templates/           # For HTML templates (analysis.html, base.html)
    |
    |--- tmp/			      # Create temp folder/files when update
        |--- new_applicant_data.json  # Output of initial clean.py
        |--- llm_cleaned.json         # Final output after LLM normalization


# load_data.py

Goal
- Load LLM-normalized JSON into PostgreSQL table `applicants` with correct types and fast bulk I/O.

Flow
1. Read JSON: load_json(path) returns list[dict].
2. Normalize fields:
  - norm_str: string.
  - to_date: date format.
  - to_float: float.
  - data_type: 14 column row aligned to schema.
3. Ensure schema: ensure_table(conn) creates `applicants` if missing with UNIQUE(url).
4. Bulk load: psycopg_pool.ConnectionPool(DSN) → cursor.copy(COPY ... FROM STDIN), write each row via cp.write_row(data_type(r)), single commit.

Design choices
- COPY over INSERT for throughput (faster).
- Centralized normalization for consistent types.
- Idempotent table creation and unique URL to prevent duplicates.
- Small pool (1–5) handles CLI and web usage without churn.

Configuration
- DSN (default local Postgres), JSON_PATH (module_2/llm_extend_applicant_data.json).


# query_data.py

Goal
- Using pooled connections, pull data query for analysis.

Queries (each opens a pooled connection)
1. count_fall_2025: COUNT(*) WHERE term='Fall 2025'.
2. percent_international: COUNT(*) FILTER WHERE International/American/Other.
3. avg_scores: AVG of GPA/GRE/GRE_V/GRE_AW with validity ranges.
4. avg_gpa_american_fall2025: AVG GPA for Americans, Fall 2025, with range filter.
5. acceptance_rate_fall2025: COUNT(Accepted) / COUNT(All) * 100 using FILTER.
6. avg_gpa_fall2025_acceptances: AVG GPA WHERE Accepted in Fall 2025.
7. count_jhu_masters_cs: COUNT(*) WHERE (JHU, CS, Masters).
8. count_gt_phd_aceept: COUNT(*) WHERE (Georgetown CS PhD acceptances in 2025).
9. degree_counts_2025: degree COUNT(*) AS num_entries WHERE 2025 - GROUP BY degree & ORDER BY.
10. top_5_programs: programs COUNT(*) AS num_entries WHERE 2025 GROUP BY programs ORDER BY (limit 5).

Main
- Executes Q1–Q10
- Cmputes percent international
- Prints output.


./app/

# __init__.py

Flow
1. create_app() constructs Flask(...).
2. Load config (SECRET_KEY) into app.config.
3. ensure_table() creates schema if missing.
4. Import and register bp from .routes (avoid circular imports).
5. Return app for the caller to use.


# clean.py & scrape.py
- Copied from module_2 assignment scripts
- Added/Changed:
  - run_clean(): create a directory (tmp) and json files with specified configuration


# db.py

Goal
- Provide a shared PostgreSQL connection pool and create the 'applicants' table if it doesn't exist.

Flow
1. Configure DSN (Postgres URL for the 'gradcafe' DB).
2. Initialize the global pool (created once at import time).
3. ensure_table(): creates schema if missing.
  - Open pooled connection and cursor.
  - Execute DDL(Data Definition Language) for applicants with columns covering raw and LLM fields.
  - Commit the transaction.

Used: __init__.py, db_helper.py, pipeline.py, routes.py

Analogy: 
  - Connection pool = the hotel
  - Connection = a room
  - Cursor = the clerk for that room
  - Transaction = room tab - all charges (queries/updates)
  - DSN: the hotel's address
  - Pool size = number of rooms


# db_helper.py

Goal
- Provide thin helpers around the shared connection pool for 
  (a) discovering which result IDs already exist and 
  (b) inserting new records idempotently.

Functions
1. existing_rids() -> set[str]
   - Ensures table exists.
   - SELECT url FROM applicants; extract the numeric id (rid).
   - Returns a set for O(1) membership checks (set/dict) during scraping/cleaning.

2. insert_records_by_url(records, mapper=data_type) -> int
   - INSERT INTO applicants with VALUES.
   - ON CONFLICT (url) DO NOTHING to avoid duplicates.
   - Uses 'mapper(record)' to coerce a dict into a 14-column tuple aligned with schema.
   - Returns count of rows actually inserted.

3. write_json(path, rows) / read_json(path)
   - Write/read json files


# routes.py

Goal
- Show analysis dashboard and provide updated data and analysis with click buttons.

Routes
1. GET /
   - Redirect to /analysis for a clean entry point.

2. GET /analysis
   - Calls query_data.py functions to compute Q1–Q10 metrics.

3. POST /pull-data
   - Run pipeline.
   - If new data exists, update.
   - If no new data exists, do nothing.

4. POST /update-analysis
   - Update analysis with current data in the database.



# pipeline.py

Goal
- Orchestrate the ETL: 
  1. Skip existing
  2. Scrape and clean
  3. LLM normalize (llm_hosting)
  4. Load to database
  5. Report a short summary

Function
run_llm_hosting()
1. Build the script path relative to this package.
2. Execute as a subprocess: python app.py --file <in_path> --out <out_path>.
3. On success: the LLM script writes out_path.
4. On failure: Capture the error, log the error, and re-raise to abort.

run_pipeline(): runs the entire ETL end to end process and returns counts and a message.
1. Discover existing IDs: exising_rids()
2. Scrape and clean: run_clean()
3. LLM normalization: run_llm_hosting()
4. Load to DB: read_json(), insert_records_by_url()

logging: to see what was happening during compilation because I was running into frequent crashes.


# static and templates: used llm to build.
  - analysis.css
  - analysis.html
  - base.html







