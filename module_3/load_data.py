import os, json, math
import psycopg_pool
import psycopg
from datetime import datetime

# Configuration
DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@localhost:5432/gradcafe")
JSON_PATH = "../module_2/llm_extend_applicant_data.json"

# ---------------------------------------------------------------------
# Load Data
# ---------------------------------------------------------------------
def load_json(path=JSON_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# ---------------------------------------------------------------------
# Date Normailzation
# ---------------------------------------------------------------------
def norm_str(value):
    if value is None:
        return ""
    else:
        return str(value).strip()

# ---------------------------------------------------------------------
# Date format
# ---------------------------------------------------------------------
def to_date(added_date):
    if not added_date:
        return ""
    
    added_date_s = added_date.strip()
    try:
        return datetime.strptime(added_date_s, "%B %d, %Y").date()
    except ValueError:
        return ""

# ---------------------------------------------------------------------
# Float format for scores
# ---------------------------------------------------------------------
def to_float(score):
    if score is None or score == "":
        return None
    
    score_s = str(score).replace("GPA", "").strip()
    try:
        score_f = float(score_s)
        if math.isfinite(score_f):
            return score_f
        else:
            return None
    except Exception:
        return None

# ---------------------------------------------------------------------
# Data Type SETUP
# ---------------------------------------------------------------------
def rowify(src: dict):
    return [
        norm_str(src.get("program")),
        norm_str(src.get("comments")),
        to_date(src.get("date_added")),
        norm_str(src.get("url")),
        norm_str(src.get("status")),
        norm_str(src.get("term")),
        norm_str(src.get("US/International")),
        to_float(src.get("GPA")),
        to_float(src.get("GRE")),
        to_float(src.get("GRE_V")),
        to_float(src.get("GRE_AW")),
        norm_str(src.get("Degree")),
        norm_str(src.get("llm-generated-program")),
        norm_str(src.get("llm-generated-university")),
    ]

def main():
    data = load_json()  # Load JSON

    pool = psycopg_pool.ConnectionPool(DSN, min_size=1, max_size=5)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            copy_sql = """
                COPY applicants (
                    program, comments, date_added, url, status, term,
                    us_or_international, gpa, gre, gre_v, gre_aw, degree,
                    llm_generated_program, llm_generated_university
                ) FROM STDIN
            """
            with cur.copy(copy_sql) as cp:
                for r in data:
                    cp.write_row(rowify(r))
        conn.commit()

    print(f"Done. Loaded {len(data)} rows")

if __name__ == "__main__":
    main()
    

