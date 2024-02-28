from pathlib import Path
import typer
from datetime import datetime, timedelta

from goodreads import GRHandler
from database import DBHandler, DBResponse
from downloader import Downloader, DownloadResponse
from book import Book
from __init__ import SUCCESS

class Goldfinch:
    def __init__(self, db_path: Path, gr_url: str, downloads_path: Path) -> None:
        self.db_handler = DBHandler(db_path)
        self.gr_handler = GRHandler(gr_url)
        self.downloader = Downloader(downloads_path)
    
    def add_book(self, title: str, author: str, date_added: str) -> int:
        """add a book to the database"""
        db_response = self.db_handler.read_db()
        if (db_response.error != SUCCESS): return db_response.error
        key = title + author
        db_response.db["undownloaded_books"][key] = {
            "title": title,
            "author": author,
            "date_added": date_added
        }
        db_response = self.db_handler.write_db(db_response.db)
        return db_response.error

    def update_db(self) -> int:
        """update the database with the books from goodreads"""
        gr_response = self.gr_handler.fetch_books()
        if (gr_response.error != SUCCESS): return gr_response.error
        db_response = self.db_handler.read_db()
        if (db_response.error != SUCCESS): return db_response.error
        for key, book in gr_response.books.items():
            if (key in db_response.db["undownloaded_books"]): continue
            if (key in db_response.db["downloaded_books"]): continue
            db_response.db["undownloaded_books"][key] = book
        db_response = self.db_handler.write_db(db_response.db)
        return db_response.error

    def download_all(self) -> int:
        """download the books from the database"""
        db_response = self.db_handler.read_db()
        if (db_response.error != SUCCESS): return db_response.error

        date_since_download = datetime.strptime(db_response.db["date_since_download"], "%m-%d-%Y")

        move_to_downloaded = []
        for key, book in db_response.db["undownloaded_books"].items():
            if (date_since_download - datetime.strptime(book["date_added"], "%m-%d-%Y") > timedelta(days=1)):
                typer.secho(f"{book["title"]} not downloaded because it was added before previous download.")
                db_response.db["downloaded_books"][key] = book
                move_to_downloaded.append(key)
                continue
            download_response = self.downloader.download(book["title"], book["author"])
            if (download_response.error != SUCCESS): 
                typer.secho(f"Error downloading {book["title"]} by {book["author"]}")
                continue
            db_response.db["downloaded_books"][key] = book
            move_to_downloaded.append(key)

        for key in move_to_downloaded:
            del db_response.db["undownloaded_books"][key]

        db_response = self.db_handler.write_db(db_response.db)
        return db_response.error
    
    def list_downloaded(self) -> int:
        """list books in downloaded"""
        pass
