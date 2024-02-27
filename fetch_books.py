import requests
from bs4 import BeautifulSoup
import datetime
import re
import json
#from datetime import date

request = requests.get("https://www.goodreads.com/review/list/119297045-claudia-k?utf8=%E2%9C%93&shelf=to-read&per_page=100")

soup = BeautifulSoup(request.content, "html.parser")
results = soup.find_all("tr", class_ = "bookalike review")

def clean_date(date: str) -> datetime.date:
    months : dict = {
        "Jan" : 1,
        "Feb" : 2,
        "Mar" : 3,
        "Apr" : 4,
        "May" : 5,
        "Jun" : 6,
        "Jul" : 7,
        "Aug" : 8,
        "Sep" : 9,
        "Oct" : 10,
        "Nov" : 11,
        "Dec" : 12
    }

    month_re = re.compile(r"([A-Za-z]{3})")
    day_re = re.compile(r"(\d{1,2})")
    year_re = re.compile(r"(\d{4})")

    month = month_re.search(date).group(1)
    day = day_re.search(date).group(1)
    year = year_re.search(date).group(1)

    return datetime.date(int(year), months[month], int(day))

books = {"books": []}

for item in results:
    title = item.find("td", class_ = "field title").text[5:].strip().replace("\n", "")
    isbn = item.find("td", class_ = "field isbn").text[4:].strip().replace("\n", "")
    date_added = item.find("td", class_ = "field date_added").text[10:].strip().replace("\n", "")
    #number = item.find("td", class_ = "field position").text.strip()

    book = {}
    book["title"] = title
    book["isbn"] = isbn
    book["date_added"] = clean_date(date_added).__str__()

    books["books"].append(book)

with open("books.json", "w") as file:
    json.dump(books, file)

##search for the book in libgen

title = books["books"][3]["title"].strip().replace(" ", "+")
url = f"https://libgen.is/fiction/?q={title}&criteria=title&language=English&format=pdf"
request = requests.get(url)
print(request)
soup = BeautifulSoup(request.content, "html.parser")
#print(soup.prettify())
table = soup.find("table", class_ = "catalog")
items = table.find_all("tr")[1:]
for item in items:
    item_title = item.find_all("td")[2].find("a").text
    if (item_title != title): continue
    mirrors = item.find_all("ul", class_ = "record_mirrors_compact")
    links = mirrors[0].find_all("li")
print(links[0].find("a")["href"])
request = requests.get(links[0].find("a")["href"])
soup = BeautifulSoup(request.content, "html.parser")
download_url = soup.find_all("div", id = "download")[0].find("a")["href"]
request = requests.get(download_url)
with open(f"{title}.pdf", "wb") as file:
    file.write(request.content)