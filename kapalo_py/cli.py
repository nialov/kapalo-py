"""
Command line integration.
"""
import typer
import kapalo_py.kapalo_map as kapalo_map
import kapalo_py.export as export
from pathlib import Path
from typing import List, Dict, Tuple
import configparser

app = typer.Typer()

EXCEPTIONS = "exceptions"
RECHECK = "recheck"


def read_config(config_path: Path) -> Tuple[Dict[str, str], List[str]]:
    """
    Read mapconfig.ini if it exists.
    """
    if not config_path.exists():
        return dict(), []

    config_parser = configparser.ConfigParser(allow_no_value=True)
    # Overwrite reading keys as lowercase
    config_parser.optionxform = lambda option: option
    config_parser.read(config_path)
    assert RECHECK in config_parser
    rechecks = list(config_parser[RECHECK].keys()) if RECHECK in config_parser else []
    exceptions = (
        dict(config_parser[EXCEPTIONS].items())
        if EXCEPTIONS in config_parser
        else dict()
    )

    return exceptions, rechecks


@app.command()
def compile_webmap(
    kapalo_sqlite_path: Path = typer.Option(
        default=Path("data/kapalo_sql/"),
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    kapalo_imgs_path: Path = typer.Option(
        default=Path("data/kapalo_imgs/"),
        exists=True,
        dir_okay=True,
    ),
    map_save_path: Path = typer.Option(default=Path("live-mapping/index.html")),
    map_imgs_path: Path = typer.Option(default=Path("live-mapping/kapalo_imgs")),
    config_path: Path = typer.Option(default=Path("mapconfig.ini")),
    project: str = typer.Option(default="Kurikka GTK"),
    add_extra: bool = typer.Option(default=True),
):
    """
    Compile live-mapping website.
    """
    exceptions, rechecks = read_config(config_path)
    kapalo_map.webmap_compilation(
        kapalo_sqlite_path=kapalo_sqlite_path,
        kapalo_imgs_path=kapalo_imgs_path,
        map_save_path=map_save_path,
        map_imgs_path=map_imgs_path,
        exceptions=exceptions,
        rechecks=rechecks,
        project=project,
        add_extra=add_extra,
    )


@app.command()
def export_observations(
    projects: List[str] = typer.Option(["Kurikka GTK"]),
    kapalo_sqlite_path: Path = typer.Option(
        default=Path("data/kapalo_sql/"),
        exists=True,
        dir_okay=False,
    ),
    export_folder: Path = typer.Option(
        default=Path("exports"),
        exists=True,
        dir_okay=True,
    ),
):
    """
    Export kapalo tables.
    """
    export.export_projects_to_folder(
        kapalo_sqlite_path=kapalo_sqlite_path,
        export_folder=export_folder,
        projects=projects,
    )
