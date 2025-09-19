"""Pipeline for scraping, cleaning, LLM normalization, and database insertion.

This module coordinates the following steps:

1. Determine which records are already in the database.
2. Scrape new survey results and write them to a temporary JSON file.
3. Run an external LLM-hosting script to normalize the data.
4. Insert normalized records into PostgreSQL.

Usage
-----

.. code-block:: python

   from app.pipeline import run_pipeline
   summary = run_pipeline(max_records=10, delay=1.0)
   print(summary["message"])
"""

import logging

from pathlib import Path
import subprocess, sys

from .db_helper import (
    existing_rids,
    read_json,
    insert_records_by_url,
    TMP_DIR
)
from .clean import run_clean
from load_data import data_type


CLEAN_JSON = TMP_DIR / "new_applicant_data.json"
FINAL_JSON = TMP_DIR / "llm_cleaned.json"

logger = logging.getLogger(__name__)

# Call llm_hosting to do the cleaning process
def run_llm_hosting(in_path: Path, out_path: Path) -> None:
    """Run the external LLM-hosting script to clean/normalize JSON.

    Calls ``llm_hosting/app.py`` as a subprocess, passing input and output
    file paths. Logs and re-raises any subprocess errors.

    :param in_path: Path to the input JSON file.
    :type in_path: pathlib.Path
    :param out_path: Path where the LLM-normalized JSON will be written.
    :type out_path: pathlib.Path
    :return: None
    :rtype: NoneType
    :raises subprocess.CalledProcessError: If the external script fails.
    """

    script = Path(__file__).resolve().parent / "llm_hosting" / "app.py"
    cmd = [sys.executable, str(script), "--file", str(in_path), "--out", str(out_path)]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        # Log the error from the external script for easier debugging
        logger.error(
            "LLM hosting script failed with exit code %s:\n%s",
            exc.returncode,
            exc.stderr,
        )
        # Re-raise the exception to stop the pipeline
        raise

# Run pipeline
def run_pipeline(max_records: int = 5, delay: float = 0.5) -> dict:
    """Run the full scraping → cleaning → LLM → database pipeline.

    Steps
    -----
    1. Skip already-existing records.
    2. Scrape new rows and save to ``CLEAN_JSON``.
    3. Run LLM-hosting to produce ``FINAL_JSON``.
    4. Insert normalized rows into the database.

    :param max_records: Maximum number of new records to scrape.
    :type max_records: int
    :param delay: Delay in seconds between scrape requests.
    :type delay: float
    :return: Summary dictionary with counts and status message.
    :rtype: dict
    """
    # 1. Skip what we already 'have'
    have = existing_rids()

    # 2. Scrape only NEW and write CLEAN_JSON (inside run_clean)
    n_clean = run_clean(
        skip_rids=have,
        max_records=max_records,
        delay=delay,
        out_filename=CLEAN_JSON.name,  # saved into TMP_DIR
    )

    if n_clean == 0:
        return {"cleaned": 0, "llm": 0, "inserted": 0, "message": "No new rows"}

    # 3. LLM hosting to produce FINAL_JSON
    run_llm_hosting(CLEAN_JSON, FINAL_JSON)
    llm_rows = read_json(FINAL_JSON)
    n_llm = len(llm_rows)

    # 4. Insert into DB
    inserted = insert_records_by_url(llm_rows, data_type)

    msg = f"Cleaned {n_clean}, LLM rows {n_llm}, inserted {inserted}"

    logging.info("Pipeline: %s", msg)

    return {"cleaned": n_clean, "llm": n_llm, "inserted": inserted, "message": msg}
