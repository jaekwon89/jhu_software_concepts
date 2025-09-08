Name: Jae Kwon (jkwon30)


Module Info: JHU EP 605.256 Module 2: Web Scraping


Approach:
scrape.py
Summary: 
  - Scrape -> Loop pages -> Extract IDs & parse partial data -> fetch detail pages -> parse text -> store as dict -> stop at record limit.

1. Built a GradCafeScraping class to handle all scraping.
   - Set BASE_URL and initialized urllib3.PoolManager for requests.
   - Added scrape_data(path) to fetch HTML and parse with BeautifulSoup.

2. Defined collect_records() to gather results across survey pages.
   - Used a seen set to avoid duplicate result IDs.
   - Extracted IDs with regex from <a> tags matching /result/{id}.
   - Pulled 'date_added' and 'term' from row_text using regex.
   - For each ID, called parse_results() to extract details.
   - Added time.sleep() between requests to stay polite.

3. Defined parse_results() to clean each result page into a dictionary.
   - Parsed fields with regex: 
	- institution 
	- program
	- degree
	- country of origin
	- GPA
	- GRE (total, verbal, AW)
	- notes (comments)
	- decision, and notification date for 'status'.
   - Combined institution + program into one field.
   - Merged listing metadata ('date_added', 'term') with detailed record to match with the sample output from assignment.

4. Tested with main().
   - Collected a few sample records.
   - Printed structured output for each record to check parsing.
   - Confirmed no duplicates, metadata merge worked, and records were consistent.

clean.py
Summary:
  - Collect raw records (GradCafeScraping) -> Normalize status field -> Save as JSON -> Reload for later use.

1. Set up configuration at the top.
   - MAX_RECORDS: Controls how many records to fetch
   - REQUEST_DELAY: delay between requests
   - OUTPUT_JSON: utput file name

2. Defined regex and helpers for status normalization.
   - STATUS_RE: matches Accepted / Rejected / Wait listed(Waitlisted) / Interviewed with optional date (dd/mm/yyyy).
   - _format_day_mon(): converts numeric date to "D Mon" (e.g., 01/03/2025 -> 1 Mar).
   - status(): builds consistent strings:
       - "Decision on D Mon" if date is present
       - "Decision" if no date
       - Falls back to raw string if pattern doesn’t match

3. Cleaning records.
   - clean_record(): copies a record and replaces the 'status' with normalized output.
   - Leaves all other fields (program, GPA, GRE, comments, etc.) unchanged.

4. Input/Output.
   - save_json(): writes list of dicts to disk with UTF-8 and pretty indenting.
   - load_data(): reloads cleaned records for later.

5. Run to get data.
   - run_clean():
       - Calls GradCafeScraping.collect_records()
       - Cleans each record with clean_record()
       - Saves results to OUTPUT_JSON
       - Prints summary line with record count

