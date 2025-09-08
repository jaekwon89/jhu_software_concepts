# clean.py
import json
import re
from datetime import datetime
from scrape import GradCafeScraping

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
MAX_RECORDS = 30000        # how many to fetch
REQUEST_DELAY = 0.3     # seconds between requests
OUTPUT_JSON = "applicant_data.json"

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

def _format_day_mon(date_str: str) -> str:
    """
    Convert numeric dd/mm/yyyy to 'D Mon' (e.g., '01/03/2025' -> '1 Mar').
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

def status(raw: str) -> str:
    """Return 'Decision on D Mon' (e.g., 'Accepted on 1 Mar')."""
    if not raw:
        return ""
    
    m = STATUS_RE.search(raw)
    
    if not m:
        return raw.strip()
    
    decision = m.group(1).strip().title()
    date_part = _format_day_mon(m.group(2) or "")
    
    return f"{decision} on {date_part}" if date_part else decision

def clean_record(rec: dict):
    rec = dict(rec)  # shallow copy
    rec["status"] = status(rec.get("status", ""))
    return rec

# ---------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------
def save_json(path: str, rows: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------
def load_data(path: str) -> list:
    """Load cleaned records later (e.g., for llm_hosting)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------
# Run samples
# ---------------------------------------------------------------------
def run_clean(
        max_records=MAX_RECORDS, 
        delay=REQUEST_DELAY, 
        out_path=OUTPUT_JSON
    ):
    scraper = GradCafeScraping()
    
    raw = scraper.collect_records(max_records=max_records, delay=delay)
    cleaned = [clean_record(r) for r in raw]
    
    save_json(out_path, cleaned)
    
    print(f"Saved {len(cleaned)} records → {out_path}")
    
    return cleaned

if __name__ == "__main__":
    # Edit the configuration above:
    run_clean(MAX_RECORDS, REQUEST_DELAY, OUTPUT_JSON)
