# goldfinch/book.py

from datetime import datetime

class Book:
    def __init__(self, title: str, author: str, date_added: datetime):
        self.title = title
        self.author = author
        self.date_added = date_added
        self.date_downloaded: datetime = None
        self.download_link: str = None