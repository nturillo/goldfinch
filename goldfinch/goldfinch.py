from pathlib import Path
import typer
from datetime import datetime, timedelta

from goodreads import GRHandler
from database import DBHandler, DBResponse
from downloader import Downloader, DownloadResponse
from book import Book
from __init__ import SUCCESS, ERRORS, NOT_IN_DB

class Goldfinch:
    def __init__(self, db_path: Path, gr_url: str, downloads_path: Path) -> None:
        self.db_handler = DBHandler(db_path)
        self.gr_handler = GRHandler(gr_url)
        self.downloader = Downloader(downloads_path)
    
    def add_book(self, title: str, author: str, date_added: str, destination: str) -> int:
        """add a book to the database"""
        db_response = self.db_handler.read_db()
        if (db_response.error != SUCCESS): return db_response.error
        key = title + author
        db_response.db[destination][key] = {
            "title": title,
            "author": author,
            "date_added": date_added
        }
        db_response = self.db_handler.write_db(db_response.db)
        return db_response.error

    def remove_book(self, title: str, author: str) -> int:
        """remove a book from the database"""
        db_response = self.db_handler.read_db()
        if (db_response.error != SUCCESS): return db_response.error

        swapped_author = author.split(", ")[1] + " " + author.split(", ")[0] if (", " in author) else author.split(" ")[1] + ", " + author.split(" ")[0]
        removed = False
        for a in [author, swapped_author]:
            key = title + a
            if (key in db_response.db["undownloaded_books"]):
                del db_response.db["undownloaded_books"][key]
                removed = True
            elif (key in db_response.db["downloaded_books"]):
                del db_response.db["downloaded_books"][key]
                removed = True
            elif (key in db_response.db["failed_books"]):
                del db_response.db["failed_books"][key]
                removed = True
            if removed: break
        if not removed: return NOT_IN_DB
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
            if (key in db_response.db["failed_books"]): continue
            db_response.db["undownloaded_books"][key] = book
        db_response = self.db_handler.write_db(db_response.db)
        return db_response.error

    def download_all(self, retry_failed: bool) -> int:
        """download the books from the database"""
        db_response = self.db_handler.read_db()
        if (db_response.error != SUCCESS): return db_response.error

        date_since_download = datetime.strptime(db_response.db["date_since_download"], "%m-%d-%Y")

        delete_from_undownloaded = []
        source = "undownloaded_books" if not retry_failed else "failed_books"
        for key, book in db_response.db[source].items():

            if (book["date_added"] is not None and date_since_download - datetime.strptime(book["date_added"], "%m-%d-%Y") > timedelta(days=1)):
                #Don't download books added before the last download
                typer.secho(f"{book["title"]} moved to downloaded because it was added before previous download.")
                db_response.db["downloaded_books"][key] = book
                delete_from_undownloaded.append(key)
                continue

            download_response = None
            try: 
                #Catch-all to ensure downloads don't stop
                #Errors should be caught within the download method, but this is a safety
                download_response = self.downloader.download(book["title"], book["author"])
            except:
                typer.secho(f"Error downloading {book["title"]} by {book["author"]}",
                            fg=typer.colors.RED)
                db_response.db["failed_books"][key] = book
                delete_from_undownloaded.append(key)
                continue

            if (download_response.error != SUCCESS): 
                typer.secho(f"Error downloading {book["title"]} by {book["author"]} because of {ERRORS[download_response.error]}",
                            fg=typer.colors.RED)
                db_response.db["failed_books"][key] = book
                delete_from_undownloaded.append(key)
                continue

            db_response.db["downloaded_books"][key] = {
                "title": book["title"],
                "author": book["author"],
                "date_added": book["date_added"],
                "date_downloaded": download_response.date_downloaded,
                "link": download_response.link
            }
            delete_from_undownloaded.append(key)
            typer.secho(f"{book["title"]} downloaded successfully",
                        fg=typer.colors.GREEN)

        for key in delete_from_undownloaded:
            if key in db_response.db["undownloaded_books"]:
                del db_response.db["undownloaded_books"][key]

        db_response = self.db_handler.write_db(db_response.db)
        return db_response.error
    
    def list(self, source : str = None) -> int:
        """list books in database"""
        db_response = self.db_handler.read_db()
        if (db_response.error != SUCCESS): return db_response.error
        if (source == None):
            typer.secho("Undownloaded Books", fg=typer.colors.GREEN)
            for key, book in db_response.db["undownloaded_books"].items():
                typer.secho(f"\t{book['title']} by {book['author']}", fg=typer.colors.WHITE)
            typer.secho("Downloaded Books", fg=typer.colors.GREEN)
            for key, book in db_response.db["downloaded_books"].items():
                typer.secho(f"\t{book['title']} by {book['author']}", fg=typer.colors.WHITE)
            typer.secho("Failed Books", fg=typer.colors.GREEN)
            for key, book in db_response.db["failed_books"].items():
                typer.secho(f"\t{book['title']} by {book['author']}", fg=typer.colors.WHITE)
        else:
            typer.secho(f"{source.replace("_", " ")} Books", fg=typer.colors.GREEN)
            for key, book in db_response.db[source].items():
                typer.secho(f"{book['title']} by {book['author']}", fg=typer.colors.WHITE)

    def get_gr_url(self) -> str:
        url = self.gr_handler.get_url()
        return url
    
    def set_gr_url(self, url: str) -> None:
        self.gr_handler.set_url(url)