import urllib3
from bs4 import BeautifulSoup
import re
import time

class GradCafeScraping:
    """Scraper for TheGradCafe survey/results pages."""

    BASE_URL = "https://www.thegradcafe.com"

    def __init__(self, base_url=BASE_URL):
        """Initialize the scraper.

        :param base_url: Base URL for the site (override for testing/mocking).
        :type base_url: str
        """
        self.base_url = base_url
        self.http = urllib3.PoolManager()
        self.survey_url = f"{self.base_url}/survey/"
        self.result_re = re.compile(r"^/result/(\d+)$")  # Search each ID

    def scrape_data(self, path="/survey/"):
        """Fetch a page and return a BeautifulSoup parser.

        :param path: Path under the base URL to fetch.
        :type path: str
        :return: Parsed HTML document.
        :rtype: bs4.BeautifulSoup
        """
        response = self.http.request("GET", self.base_url + path)
        html_text = response.data.decode("utf-8")
        return BeautifulSoup(html_text, "html.parser")
    
    def collect_records(self, max_records=150, delay=0.5, skip_rids=None):
        """Collect records by walking the survey listing pages.

        For each listing page (``/survey/`` then ``/survey/?page=N``), extract
        result IDs, visit each detail page, parse fields, and accumulate a list
        of records until ``max_records`` is reached.

        :param max_records: Maximum number of records to collect.
        :type max_records: int
        :param delay: Politeness delay (seconds) between requests.
        :type delay: float
        :param skip_rids: Set of result IDs (strings) to skip.
        :type skip_rids: set[str] or None
        :return: List of parsed result dictionaries.
        :rtype: list[dict]
        """
        if skip_rids is None:
            skip_rids = set()
        seen = set()
        records = []
        meta = {}  # reference id -> {"date_added": "...", "term": "..."}
        
        page = 1
        while len(records) < max_records:
            # Build URL: first page is plain /survey/, others use ?page=
            if page == 1:
                path = "/survey/"
            else:
                path = f"/survey/?page={page}"

            print(f"Fetching {self.base_url}{path} ...")

            soup = self.scrape_data(path)

            all_skipped = True
            
            # Extract IDs
            for a in soup.find_all("a", href=True):
                m = self.result_re.match(a["href"])
                if not m:
                    continue
                rid = m.group(1)  # rid: reference ID (Application Info)

                if rid in seen or rid in skip_rids:
                    continue
                
                all_skipped = False

                # Choose a larger ancestor that likely contains row content
                # Start from <tbody>
                container = a.find_parent('tbody') or a

                if container:
                    row_text = container.get_text(" ", strip=True)
                else:
                    row_text = a.get_text(" ", strip=True)

                # date_added e.g., "September 05, 2025"
                m_date = re.search(
                    r"(?:Added\s+on\s+)?([A-Z][a-z]+ \d{1,2}, \d{4})", row_text
                )
                date_added = m_date.group(1) if m_date else ""

                # term e.g., "Fall 2025", "Spring 2026"
                m_term = re.search(
                    r"\b(Fall|Spring|Summer|Winter)\s+20\d{2}\b", row_text, re.I
                )
                term = m_term.group(0).title() if m_term else ""

                meta = {
                    rid: {
                        "date_added": date_added, 
                        "term": term,
                        }
                    }

                # Parsing and adding meta data to the detail page
                rec = self.parse_results(rid, meta=meta)
                
                # Prevent reference ID duplicates
                records.append(rec)
                seen.add(rid)

                if len(records) >= max_records:
                    break
            
                time.sleep(delay)  # polite pause between detail fetches
            if all_skipped:
                break

            # Progress (global order number starting at 1)
            print(
                f"Order#: {len(records)}. Last Applicant ID on page{page}: {rid}"
            )

            # Stop if it reaches the limit
            if len(records) >= max_records:
                break
            
            page += 1
            time.sleep(delay)  # polite pause between listing pages

        
        return records
    

    def parse_results(self, rid: str, meta=""):
        """Scrape a single result detail page and return parsed fields.

        :param rid: Result ID (e.g., ``"123456"``).
        :type rid: str
        :param meta: Optional metadata mapping produced by listing parsing,
            of the form ``{rid: {"date_added": str, "term": str}}``. If not
            provided or mismatched, date/term are left as empty strings unless
            found on the detail page.
        :type meta: dict[str, dict] or str
        :return: A dictionary with normalized fields (program, degree, scores, etc.).
        :rtype: dict
        """
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
            "Degree": "" 
        }

        # Regex patterns
        institution_re = re.search(
            r"Institution\s*(.*?)(?=\s*Program)", text, re.I
        )
        program_re = re.search(
            r"Program\s*(.*?)(?=\s*Degree\s*Type)", text, re.I
        )
        degree_re = re.search(
            r"Degree Type\s*([A-Za-z]+)", text, re.I
        )
        origin_re = re.search(
            r"Degree's Country of Origin\s*([A-Za-z]+)", text, re.I
        )
        gpa_re = re.search(
            r"Undergrad GPA\s*(\d\.\d{1,2})", text, re.I
        )
        gre_re = re.search(
            r"GRE\s*General\s*:\s*(\d{1,3})", text, re.I
        )
        gre_v_re = re.search(
            r"GRE\s*Verbal\s*:\s*(\d{1,3})", text, re.I
        )
        gre_aw_re = re.search(
            r"Analytical\s*Writing\s*:\s*([\d\.]+)", text, re.I
        )
        notes_re = re.search(
            r"(?i)Notes\s*(.*?)\s*(?=Timeline\b|$)", text, re.I
        )
        decision_re = re.search(
            r"Decision\s*(.*?)\s*(?=Notification)", text, re.I
        )
        noti_re = re.search(
            r"Notification\s*on\s*(\d{2}/\d{2}/\d{4})", text, re.I
        )

        # Assign if matches found
        if program_re:
            data["program"] = program_re.group(1).strip()
        if degree_re:
            data["Degree"] = degree_re.group(1).strip()
        if origin_re:
            data["US/International"] = origin_re.group(1).strip()
        if gpa_re:
            data["GPA"] = "GPA " + gpa_re.group(1).strip()
        if gre_re:
            data["GRE"] = gre_re.group(1).strip()
        if gre_v_re:
            data["GRE_V"] = gre_v_re.group(1).strip()
        if gre_aw_re:
            data["GRE_AW"] = gre_aw_re.group(1).strip()
        if notes_re:
            data["comments"] = notes_re.group(1).strip()

        # Build status safely (decision + date)
        parts = []
        if decision_re:
            parts.append(decision_re.group(1).strip())
        if noti_re:
            parts.append("on " + noti_re.group(1).strip())
        data["status"] = " ".join(parts)

        # Build program safely (program, institution)
        program = []
        if program_re:
            program.append(program_re.group(1).strip())
        if institution_re:
            program.append(", " + institution_re.group(1).strip())   
        data["program"] = " ".join(program)


        # Merge listing metadata (date_added, term) if available
        if meta and rid in meta:
            m = meta[rid]
            if m.get("date_added") and not data["date_added"]:
                data["date_added"] = m["date_added"]
            if m.get("term") and not data["term"]:
                data["term"] = m["term"]
        
        return data    
