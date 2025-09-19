"""Cleaning pipeline for GradCafe scraped records.

This module provides functions for:

* Normalizing status strings (decision + date).
* Cleaning individual records.
* Running a batch cleaning pipeline with scraping, filtering, and writing to JSON.

Typical usage
-------------

.. code-block:: python

   from app.clean import run_clean
   n = run_clean(skip_rids=set(), max_records=50)
   print(f"Cleaned {n} records")
"""
import re
from datetime import datetime
from pathlib import Path

from .scrape import GradCafeScraping
from .db_helper import write_json, TMP_DIR

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
MAX_RECORDS = 100  # how many to fetch
REQUEST_DELAY = 0.5  # seconds between requests
OUTPUT_JSON = "new_applicant_data.json"

# ---------------------------------------------------------------------
# Parsing: Status (decision + date) - date modification
# ---------------------------------------------------------------------
STATUS_RE = re.compile(
    r'''(?ix)
    \b
    (Accepted|Rejected|Wait\s*listed|Waitlisted|Interview(?:ed)?)  # decision
    (?:\s*on\s*  # " on "
        (
          \d{1,2}[/]\d{1,2}(?:[/]\d{2,4})?  # dd/mm/yyyy
        )
    )?
    '''
)

# Convert numeric dd/mm/yyyy to 'D Mon' (e.g., '01/03/2025' -> '1 Mar')
def _format_day_mon(date_str: str) -> str:
    """Convert a numeric date string to ``D Mon`` format.

    Example: ``"01/03/2025"`` → ``"1 Mar"``.

    :param date_str: Raw date string, e.g., ``"01/03/2025"``.
    :type date_str: str
    :return: Formatted string or the original if parsing fails.
    :rtype: str
    """
    if not date_str:
        return ""
    
    s = date_str.strip()
    m = re.match(r'^\s*(\d{1,2})[/](\d{1,2})(?:[/](\d{4}))?\s*$', s)
    
    if not m:
        return s
    
    day = int(m.group(1))
    month_num = int(m.group(2))
    
    mon_abbrev = datetime(2000, month_num, 1).strftime('%b')
    
    return f"{day} {mon_abbrev}"

# Return 'Decision on D Mon' (e.g., 'Accepted on 1 Mar').
def status(raw: str) -> str:
    """Normalize a status string (decision + optional date).

    Example: ``"Accepted on 01/03/2025"`` → ``"Accepted on 1 Mar"``.

    :param raw: Raw status string.
    :type raw: str
    :return: Normalized status string.
    :rtype: str
    """
    if not raw:
        return ""
    
    m = STATUS_RE.search(raw)
    
    if not m:
        return raw.strip()
    
    decision = m.group(1).strip().title()
    date_part = _format_day_mon(m.group(2) or "")
    
    return f"{decision} on {date_part}" if date_part else decision

def clean_record(rec: dict):
    """Clean a single record dictionary.

    Updates the ``status`` field to a normalized format.

    :param rec: Raw record dictionary.
    :type rec: dict
    :return: Cleaned record dictionary.
    :rtype: dict
    """
    rec = dict(rec)  # shallow copy
    rec["status"] = status(rec.get("status", ""))
    return rec


# ---------------------------------------------------------------------
# Run to get data if there is any
# ---------------------------------------------------------------------
def run_clean(
        skip_rids: set[str],
        max_records=MAX_RECORDS, 
        delay=REQUEST_DELAY, 
        out_filename=OUTPUT_JSON
    ) -> int:
    """Run the cleaning pipeline.

    Steps
    -----
    1. Scrape records from GradCafe (skipping known IDs).
    2. Normalize the ``status`` field.
    3. Write results to JSON if not empty.

    :param skip_rids: Set of result IDs to skip.
    :type skip_rids: set[str]
    :param max_records: Maximum number of records to fetch.
    :type max_records: int
    :param delay: Delay (seconds) between requests.
    :type delay: float
    :param out_filename: Output JSON filename inside TMP_DIR.
    :type out_filename: str
    :return: Number of records cleaned and written.
    :rtype: int
    """
    scraper = GradCafeScraping()
    
    raw = scraper.collect_records(
        max_records=max_records, 
        delay=delay,
        skip_rids=skip_rids
    )
    cleaned = [clean_record(r) for r in raw]
    
    if cleaned:  # Only write if not empty
        out_path = TMP_DIR / out_filename
        write_json(out_path, cleaned)
        print(f"Saved {len(cleaned)} records -> {out_path}")
        return len(cleaned)

    print("No new data. Nothing written.")
    return 0

if __name__ == "__main__":
    # Edit the configuration above:
    run_clean(
        skip_rids=set(), 
        max_records=MAX_RECORDS, 
        delay=REQUEST_DELAY, 
        out_filename=OUTPUT_JSON
    )
