import urllib3
from bs4 import BeautifulSoup

class GradCafeScraping:
    BASE_URL = "https://www.thegradcafe.com/"

    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.http = urllib3.PoolManager()

    def fetch_soup(self, path="/survey/"):
        response = self.http.request("GET", self.base_url + path)
        html_text = response.data.decode("utf-8")
        return BeautifulSoup(html_text, "html.parser")



if __name__ == '__main__':
    scraper = GradCafeScraping()
    soup = scraper.fetch_soup()

    print(soup.prettify())