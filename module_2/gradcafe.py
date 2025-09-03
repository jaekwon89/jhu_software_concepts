import urllib3
from bs4 import BeautifulSoup

base_url = "https://www.thegradcafe.com/"

http = urllib3.PoolManager()
response = http.request("GET", base_url +"/survey/")


html_text = response.data.decode("utf-8")


soup = BeautifulSoup(html_text, "html.parser")

print(soup.prettify())