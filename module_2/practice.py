"""
This is where I practice module 2 materials - learn by doing it page
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup

import mechanicalsoup

base_url = "http://olympus.realpython.org"

html_page = urlopen(base_url + "/profiles")
html_text = html_page.read().decode("utf-8")

# View html
# print(html_text)

soup = BeautifulSoup(html_text, "html.parser")

"""
for link in soup.find_all("a"):
    link_url = base_url + link["href"]
    print(link_url)
"""
# 1
browser = mechanicalsoup.Browser()
url = "http://olympus.realpython.org/login"
login_page = browser.get(url)
login_html = login_page.soup

# 2
form = login_html.select("form")[0]
form.select("input")[0]["value"] = "zeus"
form.select("input")[1]["value"] = "ThunderDude"

# 3
profiles_page = browser.submit(form, login_page.url)


links = profiles_page.soup.select("a")

"""
for link in links:
    address = link["href"]
    text = link.text
    print(f"{text}: {address}")

title = profiles_page.soup.title

print(title)
"""

browser1 = mechanicalsoup.Browser()
page = browser1.get("http://olympus.realpython.org/dice")
tag = page.soup.select("#result")[0]
result = tag.text

# print(f"The result of your dice roll is: {result}")

import time

browser2 = mechanicalsoup.Browser()

for i in range(4):
    page2 = browser2.get("http://olympus.realpython.org/dice")
    tag2 = page2.soup.select("#result")[0]
    result2 = tag2.text
    print(f"The result of your dice roll is: {result2}")

    # Wait 10 seconds if this isn't the last request
    if i < 3:
        time.sleep(3)