# goldfinch/downloader.py

from pathlib import Path
import typer
from typing import NamedTuple
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from __init__ import __app_name__, SUCCESS, DOWNLOAD_ERROR, NO_RESULTS

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

    def download(self, title: str, author: str) -> DownloadResponse:
        url = f"https://libgen.is/fiction/?q={author.replace(" ", "+").replace(",", r"%2C")}&criteria=authors&language=English&format=epub"
        #print(url)
        try:
            request = requests.get(url)
        except requests.RequestException:
            return DownloadResponse(title, "", "", DOWNLOAD_ERROR)
        soup = BeautifulSoup(request.content, "html.parser")
        table = soup.find("table", class_ = "catalog")
        if (table is None): 
            return DownloadResponse(title, "", "", NO_RESULTS)
        items = table.find_all("tr")[1:]
        if (len(items) == 0): 
            return DownloadResponse(title, "", "", NO_RESULTS)
        links = []
        for item in items:
            item_title = item.find_all("td")[2].find("a").text
            if (item_title not in title and title not in item_title): continue
            mirrors = item.find_all("ul", class_ = "record_mirrors_compact")
            links = mirrors[0].find_all("li")
            break
        try:
            request = requests.get(links[0].find("a")["href"])
        except requests.RequestException:
            try:
                request = requests.get(links[1].find("a")["href"])
            except requests.RequestException:
                return DownloadResponse(title, "", "", DOWNLOAD_ERROR)
        soup = BeautifulSoup(request.content, "html.parser")
        download_url = soup.find_all("div", id = "download")[0].find("a")["href"]
        try:
            request = requests.get(download_url)
        except requests.RequestException:
            return DownloadResponse(title, "", "", DOWNLOAD_ERROR)
        download_file_path = self.downloads_path / f"{title.replace(' ', '_')}.epub"
        try:
            with open(download_file_path, "wb") as file:
                file.write(request.content)
        except OSError:
            return DownloadResponse(title, "", "", DOWNLOAD_ERROR)
        time = datetime.now()
        return DownloadResponse(title, download_file_path, time, SUCCESS)