# Had to spend much more time to learn and create the pipeline

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
