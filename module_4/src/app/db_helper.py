"""Database utilities for working with applicant records.

This module provides helpers for:

* Checking existing result IDs in the database.
* Inserting new records (with URL uniqueness).
* Reading/writing JSON files for intermediate pipeline steps.

It depends on the global PostgreSQL connection pool defined in :mod:`db`.
"""

from pathlib import Path
import json
from .db import pool, ensure_table
from load_data import data_type

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
