# goldfinch/goodreads.py

import requests
from bs4 import BeautifulSoup
from typing import Dict, NamedTuple
from datetime import datetime
import re

from __init__ import GR_ERROR, SUCCESS

class GRResponse(NamedTuple):
    error: int
    books: Dict[str, Dict[str, str]]

class GRHandler():
    def __init__(self, gr_url: str) -> None:
        self.url = gr_url

    def get_url(self) -> str:
        return self.url
    
    def set_url(self, new_url: str) -> None:
        print(new_url)
        self.url = new_url
    
    def fetch_books(self) -> GRResponse:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
            request = requests.get(self.url, headers=headers)
        except requests.RequestException:
            return GRResponse(GR_ERROR, {})
        if (request.status_code != 200): 
            return GRResponse(GR_ERROR, {})
        soup = BeautifulSoup(request.content, "html.parser")
        results = soup.find_all("tr", class_ = "bookalike review")
        books = {}
        for item in results:
            title = item.find("td", class_ = "field title").text[5:].strip().replace("\n", "")
            brackets_pattern = re.compile(r"[\[({].*[\])}]")
            title = brackets_pattern.sub("", title).strip()

            author = item.find("td", class_ = "field author").text[6:].strip().replace("\n", "")
            author = author.replace("*", "")
            
            date_added = item.find("td", class_ = "field date_added").text[10:].strip().replace("\n", "")
            date_time = datetime.strptime(date_added, "%b %d, %Y")
            date_added = date_time.strftime("%m-%d-%Y")

            key = title + author
            books[key] = {
                "title": title,
                "author": author,
                "date_added": date_added
            }
        return GRResponse(SUCCESS, books)
