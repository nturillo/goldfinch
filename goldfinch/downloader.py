# goldfinch/downloader.py

from pathlib import Path
import typer
from typing import NamedTuple
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse

from __init__ import __app_name__, SUCCESS, DOWNLOAD_ERROR, NO_RESULTS, CANT_REACH_LIBGEN

DEFAULT_DOWNLOADS_DIR = Path.home() / "goldfinch_book_downloads"

def init_downloads_dir(downloads_path: Path) -> int:
    """Initialize the downloads directory."""
    try:
        downloads_path.mkdir(exist_ok=True)
    except OSError:
        return DOWNLOAD_ERROR
    return SUCCESS

class DownloadResponse(NamedTuple):
    title: str
    link: str
    date_downloaded: str
    error: int

class Downloader:
    def __init__(self, downloads_path: Path) -> None:
        self.downloads_path = downloads_path
    
    def try_url_download(self, urls, download_path: Path) -> str:
        for url in urls:
            typer.secho(f"Trying url: {url}", fg=typer.colors.BRIGHT_CYAN)
            try:
                request = requests.get(url)
                soup = BeautifulSoup(request.content, "html.parser")
                download_url = soup.find_all("div", id = "download")[0].find("a")["href"]
                request = requests.get(download_url)
            except requests.RequestException:
                continue
            if (request.status_code != 200): continue
            with open(download_path, "wb") as file:
                file.write(request.content)
            return f"{url}"
        return ""

    class SearchResponse(NamedTuple):
        links: str
        error: int
    
    (AUTHOR, BOTH, TITLE) = range(3)
    (FICTION, NONFICTION) = range(2)
    CRITERIA = {
        AUTHOR : "authors",
        TITLE : "title",
        BOTH : "",
    }

    def search_libgen(self, title: str, author: str, criteria: int, locale: int) -> SearchResponse:
        """search for a book by author on libgen.is"""

        ## URL encode the search terms
        url_author = urllib.parse.quote(author)
        url_title = urllib.parse.quote(title)
        search_term = ""
        match criteria:
            case Downloader.AUTHOR:
                search_term = url_author
            case Downloader.TITLE:
                search_term = url_title
            case Downloader.BOTH:
                search_term = url_author + "+" + url_title

        url = ""
        match locale:
            case Downloader.FICTION:
                url = f"https://libgen.is/fiction/?q={search_term}&criteria={Downloader.CRITERIA[criteria]}&language=English&format=epub"
            case Downloader.NONFICTION:
                url = f"https://libgen.is/search.php?req={search_term}&open=0&res=100&view=simple&phrase=1&column=def"

        try:
            request = requests.get(url)
        except requests.RequestException:
            return Downloader.SearchResponse("", CANT_REACH_LIBGEN)
        
        soup = BeautifulSoup(request.content, "html.parser")
        table = soup.find("table", class_ = "catalog" if locale == Downloader.FICTION else "c")
        if (table is None): 
            return Downloader.SearchResponse("", NO_RESULTS)
        items = table.find_all("tr")[1:]
        if (len(items) == 0): 
            return Downloader.SearchResponse("", NO_RESULTS)
        return_links = []
        for item in items:
            item_title = item.find_all("td")[2].find("a").text
            if (item_title not in title and title not in item_title): continue
            mirrors = item.find_all("ul", class_ = "record_mirrors_compact") if locale == Downloader.FICTION else item.find_all("td")[9:10]
            links = mirrors[0].find_all("li") if locale == Downloader.FICTION else mirrors
            return_links.append(links[0].find("a")["href"])
        return Downloader.SearchResponse(return_links, SUCCESS)


    def download(self, title: str, author: str) -> DownloadResponse:
        """main function for downloading books from libgen.is"""
        download_file_path = self.downloads_path / f"{title.replace(' ', '_')}.epub"
        
        typer.secho(f"Searching for {title} by {author} in fiction", fg=typer.colors.BRIGHT_CYAN)
        for i in range(3):
            search_response_title = self.search_libgen(title, author, i, Downloader.FICTION)
            if (search_response_title.error == CANT_REACH_LIBGEN): return DownloadResponse(title, "", "", CANT_REACH_LIBGEN)
            if (search_response_title.error == SUCCESS):
                download_try = self.try_url_download(search_response_title.links, download_file_path)
                if (download_try != ""):
                    time = datetime.now()
                    time_str = time.strftime(r"%m-%d-%Y %H:%M:%S")
                    return DownloadResponse(title, download_try, time_str, SUCCESS)
        
        typer.secho(f"Searching for {title} by {author} in nonfiction", fg=typer.colors.BRIGHT_CYAN)
        for i in range(3):
            search_response_title = self.search_libgen(title, author, i, Downloader.NONFICTION)
            if (search_response_title.error == CANT_REACH_LIBGEN): return DownloadResponse(title, "", "", CANT_REACH_LIBGEN)
            if (search_response_title.error == SUCCESS):
                download_try = self.try_url_download(search_response_title.links, download_file_path)
                if (download_try != ""):
                    time = datetime.now()
                    time_str = time.strftime(r"%m-%d-%Y %H:%M:%S")
                    return DownloadResponse(title, download_try, time_str, SUCCESS)

        return DownloadResponse(title, "", "", DOWNLOAD_ERROR)