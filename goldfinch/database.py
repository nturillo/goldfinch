# goldfinch/database.py

import configparser
from pathlib import Path
import json
from datetime import datetime
import typer
from typing import NamedTuple, Dict, Any
import book

from __init__ import JSON_ERROR, DB_ERROR, SUCCESS, __app_name__

DEFAULT_DB_PATH = Path(typer.get_app_dir(__app_name__)) / "database.json"
DEFAULT_DATE_SINCE_UPDATE = "01-01-2000"


def get_database_path(config_file: Path) -> Path:
    """Return the current path to the to-do database."""
    config_parser = configparser.ConfigParser()
    config_parser.read(config_file)
    return Path(config_parser["database"]["path"])

def init_database(db_path: Path, date_since_download: str) -> int:
    """Create the to-do database."""
    db = {
        "undownloaded_books": {},
        "downloaded_books": {},
        "date_since_download": date_since_download
    }
    try:
        with db_path.open("w") as file:
            json.dump(db, file)
        return SUCCESS
    except OSError:
        return DB_ERROR

class DBResponse(NamedTuple):
    db: Dict[str, Any]
    error: int

class DBHandler:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
    
    def read_db(self) -> DBResponse:
        try:
            with self.db_path.open("r") as db:
                try:
                    return DBResponse(json.load(db), SUCCESS)
                except json.JSONDecodeError:  # Catch wrong JSON format
                    return DBResponse([], JSON_ERROR)
        except OSError:  # Catch file IO problems
            return DBResponse([], DB_ERROR)

    def write_db(self, db : Dict[str, Any]) -> DBResponse:
        try:
            with self.db_path.open("w") as db_file:
                json.dump(db, db_file, indent=4)
            return DBResponse(db, SUCCESS)
        except OSError:  # Catch file IO problems
            return DBResponse(db, DB_ERROR)
    