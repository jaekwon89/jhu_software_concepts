Name: Jae Kwon (jkwon30)


Module Info: JHU EP 605.256 Module 3: SQL Data Analysis


Approach:
Blueprint: 
module_3/
|--- __init__.py              # Make module_3 a package
|--- run.py                   # Main entry point (runs web server or pipeline)
|--- load_data.py             # Helper for formatting data before DB insert
|--- query_data.py            # Functions for all SQL database queries to print output
|
|--- app/
    |--- __init__.py          # Create app
    |--- routes.py            # Defines all web routes and request handlers
    |--- db.py                # Database connection pool and table schema
    |--- db_helper.py         # DB helpers (insert_records_by_url)
    |--- pipeline.py          # Main pipeline orchestrator (scrape -> clean -> LLM -> load)
    |--- scrape.py            # Fetches raw data from the web (new data)
    |--- clean.py             # Cleans raw data (status, dates)
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





