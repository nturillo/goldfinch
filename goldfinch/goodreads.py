# goldfinch/goodreads.py

import requests
from bs4 import BeautifulSoup
from typing import Dict, NamedTuple
from datetime import datetime

from __init__ import GR_ERROR, SUCCESS

class GRResponse(NamedTuple):
    error: int
    books: Dict[str, Dict[str, str]]

class GRHandler():
    def __init__(self, gr_url: str) -> None:
        self.url = gr_url
    
    def fetch_books(self) -> GRResponse:
        try:
            request = requests.get(self.url)
        except requests.RequestException:
            return GRResponse(GR_ERROR, {})
        soup = BeautifulSoup(request.content, "html.parser")
        results = soup.find_all("tr", class_ = "bookalike review")
        books = {}
        for item in results:
            title = item.find("td", class_ = "field title").text[5:].strip().replace("\n", "")

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
