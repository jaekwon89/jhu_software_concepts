from __future__ import annotations
from pathlib import Path
import subprocess, sys
import logging

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_llm_hosting(in_path: Path, out_path: Path) -> None:
    """
    Call your LLM hosting script to enrich/normalize the cleaned JSON.
    """
    script = Path(__file__).resolve().parent / "llm_hosting" / "app.py"
    cmd = [sys.executable, str(script), "--file", str(in_path), "--out", str(out_path)]
    
    # Add a try...except block to gracefully handle script failures
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        # Log the error from the external script for easier debugging
        logging.error(
            f"LLM hosting script failed with exit code {e.returncode}:\n{e.stderr}"
        )
        # Re-raise the exception to stop the pipeline
        raise


def run_pipeline(max_records: int = 5, delay: float = 0.5) -> dict:
    """
    Full pipeline:
      - figure out existing rids in DB
      - scrape+clean only NEW rows → CLEAN_JSON
      - LLM-hosting second clean → FINAL_JSON
      - load final JSON into DB (ON CONFLICT(url) DO NOTHING)
    Returns a summary dict for UI/CLI.
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
    #current_app.logger.info("Pipeline: %s", msg)
    logging.info("Pipeline: %s", msg)

    return {"cleaned": n_clean, "llm": n_llm, "inserted": inserted, "message": msg}
