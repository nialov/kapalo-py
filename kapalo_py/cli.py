"""
Command line integration.
"""
import typer
import kapalo_py.kapalo_map as kapalo_map
from pathlib import Path

app = typer.Typer()


@app.command()
def compile_webmap(
    kapalo_sqlite_path: Path = typer.Option(
        default=Path("data/kapalo_sql/kapalo.sqlite"),
        exists=True,
        dir_okay=False,
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
