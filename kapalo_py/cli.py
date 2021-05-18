"""
Command line integration.
"""
import typer
import kapalo_py.kapalo_map as kapalo_map
import kapalo_py.export as export
from pathlib import Path
from typing import List

app = typer.Typer()


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
):
    """
    Compile live-mapping website.
    """
    kapalo_map.webmap_compilation(
        kapalo_sqlite_path=kapalo_sqlite_path,
        kapalo_imgs_path=kapalo_imgs_path,
        map_save_path=map_save_path,
        map_imgs_path=map_imgs_path,
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
