import urllib3
from bs4 import BeautifulSoup
import re
import json

class GradCafeScraping:
    BASE_URL = "https://www.thegradcafe.com"

    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.http = urllib3.PoolManager()

    def scrape_data(self, path="/survey/"):

        response = self.http.request("GET", self.base_url + path)
        html_text = response.data.decode("utf-8")
        return BeautifulSoup(html_text, "html.parser")
    
    def parse_results(self, path="/survey/"):
        soup = self.scrape_data(path)
        table = soup.find("tbody")
        table_text = table.get_text()

        
        

if __name__ == '__main__':
    scraper = GradCafeScraping()
    soup = scraper.scrape_data()

    all_entries = []

    text = soup.get_text()
    div = soup.select_one("div.tw-inline-block.tw-min-w-full.tw-py-2.tw-align-middle")
    div_text = div.get_text()
    table = soup.find("tbody")
    rows = table.find_all("tr")

    first_row = rows[0]
    example_row = rows[24]

    cells_in_first_row = first_row.find_all("td")
    cells_in_example_row = example_row.find_all("td")

    for i, cell in enumerate(cells_in_example_row):
        # Use strip=True to remove leading/trailing whitespace
        cell_text = cell.get_text(strip=True)
        print(f"Cell {i}: {cell_text}")


