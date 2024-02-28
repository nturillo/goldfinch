import goldfinch
from downloader import Downloader

from pathlib import Path

download_path = Path("test_downloads")

downloader = Downloader(download_path)

response = downloader.download("The Hobbit", "J.R.R. Tolkien")
print(response)