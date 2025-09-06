import urllib3
from bs4 import BeautifulSoup
import re
import mechanicalsoup
import time

class GradCafeScraping:
    BASE_URL = "https://www.thegradcafe.com"

    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.http = urllib3.PoolManager()
        self.survey_url = f"{self.base_url}/survey/"
        self.result_re = re.compile(r"^/result/(\d+)$")  # Search each ID

    def scrape_data(self, path="/survey/"):
        response = self.http.request("GET", self.base_url + path)
        html_text = response.data.decode("utf-8")
        return BeautifulSoup(html_text, "html.parser")
    
    def collect_ids(self, max_ids=50, delay=1):
        browser = mechanicalsoup.StatefulBrowser(
            soup_config={"features": "html.parser"},
            raise_on_404=True
        )
        
        seen = set()
        ids = []
        page = 1
        
        while len(ids) < max_ids:
            # Build URL: first page is plain /survey/, others use ?page=
            if page == 1:
                url = self.survey_url
            else:
                url = f"{self.survey_url}?page={page}"

            print("Fetching {} ...".format(url))

            browser.open(url)
            soup = browser.page
            
            # Extract IDs
            for a in soup.find_all("a", href=True):
                m = self.result_re.match(a["href"])
                if m:
                    rid = m.group(1)
                    if rid not in seen:
                        seen.add(rid)
                        ids.append(rid)
                        if len(ids) >= max_ids:
                            break
            
            # Stop if it reaches the limit
            if len(ids) >= max_ids:
                break
            
            page += 1
            time.sleep(delay)  # be polite
        
        return ids
    
    def parse_results(self, path="/survey/"):
        
        soup = self.scrape_data(path)
        table = soup.find("tbody")
        table_text = table.get_text()

        return table_text

        
    
if __name__ == '__main__':
    scraper = GradCafeScraping()
    ids = scraper.collect_ids(50,1)
    soup = scraper.scrape_data()
    
    #browser = mechanicalsoup.StatefulBrowser()
    #url = BASE_URL + "/survey/"

    all_entries = []

    text = soup.get_text(strip=True)

    print(ids[0])




