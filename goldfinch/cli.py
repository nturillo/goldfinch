# goldfinch/cli.py

from typing import Optional
from typing_extensions import Annotated

import typer
from pathlib import Path

from __init__ import __version__, __app_name__, ERRORS
from database import DEFAULT_DB_PATH, DEFAULT_DATE_SINCE_UPDATE
from downloader import init_downloads_dir, DEFAULT_DOWNLOADS_DIR
import config
import database
import goldfinch

app = typer.Typer(add_completion=False)

@app.command()
def init(
    gr_url: Annotated[str, typer.Argument(help="your Goodreads shelf URL\nin the form \"url\"")],
    date_since_download: Annotated[str, typer.Option("--date", "-d", help = "date since last update performed\nin the form MM-DD-YYYY")] = DEFAULT_DATE_SINCE_UPDATE, 
    db_path: Annotated[str, typer.Option("--db_path", help="path to database.json")] = DEFAULT_DB_PATH,
    downloads_path: Annotated[str, typer.Option("--downloads_path", help="path to downloads directory")] = DEFAULT_DOWNLOADS_DIR
    ) -> None:
    """Initialize the config file and book database"""
    gr_url = gr_url.replace("%", "%%")
    app_init_error = config.init_app(db_path, gr_url, downloads_path)
    if app_init_error:
        typer.secho(
            f'Creating config file failed with "{ERRORS[app_init_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    db_init_error = database.init_database(Path(db_path), date_since_download)
    if db_init_error:
        typer.secho(
            f'Creating database failed with "{ERRORS[db_init_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    downloads_init_error = init_downloads_dir(Path(downloads_path))
    if downloads_init_error:
        typer.secho(
            f'Creating downloads directory failed with "{ERRORS[downloads_init_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    typer.secho(f"Config file created at {config.CONFIG_FILE_PATH}", fg=typer.colors.GREEN)
    typer.secho(f"The database is {db_path}", fg=typer.colors.GREEN)
    typer.secho(f"Downloads directory created at {downloads_path}", fg=typer.colors.GREEN)
    raise typer.Exit(1)


def get_goldfinch() -> goldfinch.Goldfinch:
    config_parser = config.get_config_parser()
    db_path = Path(config_parser["General"]["database_path"])
    gr_url = config_parser["General"]["goodreads_url"]
    downloads_path = Path(config_parser["General"]["downloads_path"])
    return goldfinch.Goldfinch(db_path, gr_url, downloads_path)

@app.command()
def update() -> None:
    goldfinch = get_goldfinch()
    update_error = goldfinch.update_db()
    if update_error:
        typer.secho(
            f"update failed with {ERRORS[update_error]}",
            fg=typer.colors.RED
        )
    typer.secho(f"Database updated")

@app.command()
def download(
    retry_failed: Annotated[bool, typer.Option("--retry", "-r", help="Retry failed downloads. Will not download new books.")] = False,
) -> None:
    goldfinch = get_goldfinch()
    download_error = goldfinch.download_all(retry_failed)
    if download_error:
        typer.secho(
            f"downloads failed with {ERRORS[download_error]}",
            fg=typer.colors.RED
        )
    typer.secho(f"Downloads complete")