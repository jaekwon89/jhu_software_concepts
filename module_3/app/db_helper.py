from pathlib import Path
import json
from .db import pool, ensure_table
from load_data import data_type

# Temp directory for intermediate files.
TMP_DIR = Path(__file__).resolve().parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)

# Return rids already stored (derived from URL).
def existing_rids() -> set[str]:
    ensure_table()  # Make sure the table exists before SELECTing.
    urls = []
    rids = set()

    # Use a pooled connection/cursor; context managers ensure cleanup.
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT url FROM applicants")
        for row in cur.fetchall():
            urls.append(row[0])
    
    for url in urls:
        if url:
            rid = url.rsplit("/", 1)[-1]  # Split to get the ID
            rids.add(rid)
    
    return rids
    
# Insert records using a unique URL, ignoring duplicates.
def insert_records_by_url(records: list[dict], data_type) -> int:
    if not records:
        return 0

    cols = (
        "program","comments","date_added","url","status","term",
        "us_or_international","gpa","gre","gre_v","gre_aw","degree",
        "llm_generated_program","llm_generated_university"
    )
    placeholders = ", ".join(["%s"] * len(cols))
    sql = (
        f"INSERT INTO applicants ({', '.join(cols)}) "
        f"VALUES ({placeholders}) "
        "ON CONFLICT (url) DO NOTHING"  # Skip duplicates by URL
    )

    inserted = 0
    with pool.connection() as conn, conn.cursor() as cur:
        for record in records:
            cur.execute(sql, data_type(record))
            # rowcount==1 only when the row was inserted
            if cur.rowcount == 1:
                inserted += 1
        conn.commit()  # one commit for the batch
    return inserted

# Write a list of dicts to a pretty-printed JSON file.
def write_json(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

# READ json/jsonl file
def read_json(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows
