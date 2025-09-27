"""Database utilities for working with applicant records.

This module provides helpers for:

* Checking existing result IDs in the database.
* Inserting new records (with URL uniqueness).
* Reading/writing JSON files for intermediate pipeline steps.

It depends on the global PostgreSQL connection pool defined in :mod:`db`.
"""

from pathlib import Path
import json
from psycopg import sql
from ..load_data import data_type
from .db import pool, ensure_table

# Temp directory for intermediate files.
TMP_DIR = Path(__file__).resolve().parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)


# Return rids already stored (derived from URL).
def existing_rids() -> set[str]:
    """Return the set of reference IDs (``rid``) already stored.

    Extracts IDs from the ``url`` field in the ``applicants`` table.

    :return: Set of unique reference IDs.
    :rtype: set[str]
    """
    ensure_table()  # Make sure the table exists before SELECTing.
    rids = set()

    # Separate the SQL statement from the execution.
    # Use sql.SQL for the template and sql.Identifier for table/column names.
    query = sql.SQL("SELECT {column} FROM {table} LIMIT %s")
    # Convert inputs (table/column names) into formatted identifiers.
    formatted_query = query.format(
        column=sql.Identifier('url'),
        table=sql.Identifier('applicants')
    )
    # This prevents accidentally fetching an uncontrollably large dataset.
    query_limit = 10000

    # Use a pooled connection/cursor; context managers ensure cleanup.
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(formatted_query, (query_limit,))
        urls = [row[0] for row in cur.fetchall()]
    for url in urls:
        if url:
            try:
                # Split to get the ID
                rid = url.rsplit("/", 1)[-1]
                rids.add(rid)
            except IndexError:
                # Handle cases where the URL might not have a '/'
                print(f"Warning: Could not parse rid from URL: {url}")
    return rids

# Insert records using a unique URL, ignoring duplicates.
def insert_records_by_url(records: list[dict]) -> int:
    """Insert applicant records into the database.

    Uses ``ON CONFLICT (url) DO NOTHING`` to skip duplicates
    (uniqueness is enforced by ``url``).

    :param records: List of record dictionaries to insert.
    :type records: list[dict]
    :param data_type: Function that converts a record dict into
                      a list of values matching the schema.
    :type data_type: callable
    :return: Number of rows successfully inserted.
    :rtype: int
    """
    if not records:  # pragma: no cover
        return 0

    cols = (
        "program",
        "comments",
        "date_added",
        "url",
        "status",
        "term",
        "us_or_international",
        "gpa",
        "gre",
        "gre_v",
        "gre_aw",
        "degree",
        "llm_generated_program",
        "llm_generated_university",
    )
    col_list = sql.SQL(", ").join(sql.Identifier(c) for c in cols)
    val_list = sql.SQL(", ").join(sql.Placeholder(c) for c in cols)

    stmt = sql.SQL("""
        INSERT INTO {tbl} ({cols})
        VALUES ({vals})
        ON CONFLICT ({conf}) DO NOTHING
    """).format(
        tbl=sql.Identifier("applicants"),
        cols=col_list,
        vals=val_list,
        conf=sql.Identifier("url"),
    )

    inserted = 0
    with pool.connection() as conn, conn.cursor() as cur:
        for record in records:
            cur.execute(stmt, data_type(record))   # dict mapping matches placeholders
            if cur.rowcount == 1:
                inserted += 1
        conn.commit()
    return inserted


# Write a list of dicts to a pretty-printed JSON file.
def write_json(path: Path, rows: list[dict]) -> None:
    """Write a list of dicts to a pretty-printed JSON file.

    :param path: Path to the file to write.
    :type path: pathlib.Path
    :param rows: List of row dicts to serialize.
    :type rows: list[dict]
    :return: None
    :rtype: NoneType
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


# READ json/jsonl file
def read_json(path: Path) -> list[dict]:
    """Read a JSON or JSONL file into a list of dicts.

    Supports both JSON (array of objects) and JSON Lines (one object per line).

    :param path: Path to the JSON or JSONL file.
    :type path: pathlib.Path
    :return: List of records parsed from the file.
    :rtype: list[dict]
    """
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows
