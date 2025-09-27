# pylint: disable=missing-function-docstring
"""Scraping utilities for pulling and parsing external pages safely."""

from typing import Dict, Optional, Tuple
import re
import time

import urllib3
from bs4 import BeautifulSoup

# Compile patterns once (fewer locals & branches in functions)
RESULT_RE = re.compile(r"^/result/(\d+)$")
DATE_ADDED_RE = re.compile(r"(?:Added\s+on\s+)?([A-Z][a-z]+ \d{1,2}, \d{4})")
TERM_RE = re.compile(r"\b(Fall|Spring|Summer|Winter)\s+20\d{2}\b", re.I)

INSTITUTION_RE = re.compile(r"Institution\s*(.*?)(?=\s*Program)", re.I)
PROGRAM_RE = re.compile(r"Program\s*(.*?)(?=\s*Degree\s*Type)", re.I)
DEGREE_RE = re.compile(r"Degree Type\s*([A-Za-z]+)", re.I)
ORIGIN_RE = re.compile(r"Degree's Country of Origin\s*([A-Za-z]+)", re.I)
GPA_RE = re.compile(r"Undergrad GPA\s*(\d\.\d{1,2})", re.I)
GRE_RE = re.compile(r"GRE\s*General\s*:\s*(\d{1,3})", re.I)
GRE_V_RE = re.compile(r"GRE\s*Verbal\s*:\s*(\d{1,3})", re.I)
GRE_AW_RE = re.compile(r"Analytical\s*Writing\s*:\s*([\d\.]+)", re.I)
NOTES_RE = re.compile(r"(?i)Notes\s*(.*?)\s*(?=Timeline\b|$)", re.I)
DECISION_RE = re.compile(r"Decision\s*(.*?)\s*(?=Notification)", re.I)
NOTI_RE = re.compile(r"Notification\s*on\s*(\d{2}/\d{2}/\d{4})", re.I)


def _match_text(pattern: re.Pattern[str], text: str) -> str:
    """Return the first capturing group (stripped) or '' if not found."""
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _extract_date_term(row_text: str) -> Tuple[str, str]:
    """Pull date_added and term from a survey row's text."""
    date_added = _match_text(DATE_ADDED_RE, row_text)
    term_match = TERM_RE.search(row_text)
    term = term_match.group(0).title() if term_match else ""
    return date_added, term


class GradCafeScraping:
    """Scraper for TheGradCafe survey/results pages."""

    BASE_URL = "https://www.thegradcafe.com"

    def __init__(self, base_url: str = BASE_URL):
        """Initialize the scraper.

        :param base_url: Base URL for the site (override for testing/mocking).
        """
        self.base_url = base_url
        self.http = urllib3.PoolManager()
        self.survey_url = f"{self.base_url}/survey/"

    def scrape_data(self, path: str = "/survey/") -> BeautifulSoup:
        """Fetch a page and return a BeautifulSoup parser."""
        response = self.http.request("GET", self.base_url + path)
        html_text = response.data.decode("utf-8")
        return BeautifulSoup(html_text, "html.parser")

    def collect_records(  # pylint: disable=too-many-locals
        self,
        max_records: int = 150,
        delay: float = 0.5,
        skip_rids: Optional[set[str]] = None,
    ) -> list[dict]:
        """Collect records by walking the survey listing pages."""
        skip = set(skip_rids or ())
        seen: set[str] = set()
        records: list[dict] = []

        page = 1
        while len(records) < max_records:
            path = "/survey/" if page == 1 else f"/survey/?page={page}"
            soup = self.scrape_data(path)

            found_any = False
            for a in soup.find_all("a", href=True):
                m = RESULT_RE.match(a["href"])
                if not m:
                    continue

                rid = m.group(1)
                if rid in seen or rid in skip:
                    continue

                found_any = True

                # Pull a fuller row of text (prefer a table body row)
                container = a.find_parent("tbody") or a
                row_text = container.get_text(" ", strip=True)
                date_added, term = _extract_date_term(row_text)

                rid_meta = {rid: {"date_added": date_added, "term": term}}
                records.append(self.parse_results(rid, meta=rid_meta))
                seen.add(rid)

                if len(records) >= max_records:
                    break
                time.sleep(delay)

            if not found_any:
                break

            page += 1
            time.sleep(delay)

        return records

    def parse_results(  # pylint: disable=too-many-locals, too-many-branches
        self,
        rid: str,
        meta: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> dict:
        """Scrape a single result detail page and return parsed fields."""
        soup = self.scrape_data(f"/result/{rid}")
        text = soup.get_text(" ", strip=True)

        data = {
            "program": "",
            "comments": "",
            "date_added": "",
            "url": f"{self.base_url}/result/{rid}",
            "status": "",
            "term": "",
            "US/International": "",
            "GRE": "",
            "GRE_V": "",
            "GRE_AW": "",
            "GPA": "",
            "Degree": "",
        }

        # Simple field extraction via table-driven mapping (fewer branches)
        fields = (
            ("Degree", DEGREE_RE, None),
            ("US/International", ORIGIN_RE, None),
            ("GPA", GPA_RE, "GPA "),
            ("GRE", GRE_RE, None),
            ("GRE_V", GRE_V_RE, None),
            ("GRE_AW", GRE_AW_RE, None),
            ("comments", NOTES_RE, None),
        )
        for key, pattern, prefix in fields:
            val = _match_text(pattern, text)
            if val:
                data[key] = (prefix or "") + val

        # Program (program + institution, joined nicely)
        prog = _match_text(PROGRAM_RE, text)
        inst = _match_text(INSTITUTION_RE, text)
        parts = [p for p in (prog, inst) if p]
        if parts:
            data["program"] = ", ".join(parts)

        # Status (decision + notification date)
        decision = _match_text(DECISION_RE, text)
        notif = _match_text(NOTI_RE, text)
        status_parts = []
        if decision:
            status_parts.append(decision)
        if notif:
            status_parts.append(f"on {notif}")
        data["status"] = " ".join(status_parts)

        # Merge listing metadata when available
        if meta and rid in meta:
            m = meta[rid]
            if not data["date_added"]:
                data["date_added"] = m.get("date_added", "")
            if not data["term"]:
                data["term"] = m.get("term", "")

        return data
