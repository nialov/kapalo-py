"""
Command line integration.
"""
import configparser
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import typer
from PIL import Image

from kapalo_py import export, kapalo_map, utils

app = typer.Typer()

EXCEPTIONS = "exceptions"
RECHECK = "recheck"
RCLONE = "rclone"
SYNC = "sync"

IMGS_DIR = "kapalo_imgs"
SQL_DIR = "kapalo_sql"

DATA_SQL_DIR_PATH = f"data/{SQL_DIR}"
DATA_IMGS_DIR_PATH = f"data/{IMGS_DIR}"
# styles.css is included with pyproject.toml
LOCAL_STYLESHEET = f"{Path(__file__).parent.parent.resolve()}/styles.css"
INDEX_HTML = "index.html"
MAPCONFIG = "mapconfig.ini"


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
        default=DATA_SQL_DIR_PATH,
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    kapalo_imgs_path: Path = typer.Option(
        default=Path(DATA_IMGS_DIR_PATH),
        exists=True,
        dir_okay=True,
    ),
    map_save_path: Path = typer.Option(default=Path(INDEX_HTML), dir_okay=False),
    config_path: Path = typer.Option(default=Path(MAPCONFIG)),
    projects: List[str] = typer.Option(["Kurikka GTK"]),
    stylesheet: Path = typer.Option(LOCAL_STYLESHEET, exists=True, dir_okay=False),
    extra_datasets: List[Path] = typer.Option(
        [],
        exists=True,
        help=(
            "Extra geodatasets to add to map."
            " Can give multiple but note that the other extra_* arguments must"
            " be given in same order."
        ),
        dir_okay=False,
    ),
    extra_names: List[str] = typer.Option([], help="Names for extra geodatasets."),
    extra_popup_fields: List[str] = typer.Option(
        [], help="Field in each geodataset to show in map popup."
    ),
    extra_style_functions: List[utils.StyleFunctionEnum] = typer.Option(
        [],
        help="Choose function to visualize each geodataset or leave empty for default.",
    ),
    extra_colors: List[str] = typer.Option(
        [],
        help="Choose colors for each geodataset.",
    ),
):
    """
    Compile live-mapping website.
    """
    exceptions, rechecks = read_config(config_path)
    kapalo_map.webmap_compilation(
        kapalo_sqlite_path=kapalo_sqlite_path,
        kapalo_imgs_path=kapalo_imgs_path,
        map_save_path=map_save_path,
        exceptions=exceptions,
        rechecks=rechecks,
        projects=projects,
        extra_datasets=extra_datasets,
        extra_names=extra_names,
        extra_popup_fields=extra_popup_fields,
        extra_style_functions=[
            utils.StyleFunctionEnum.style_function(enum)
            for enum in extra_style_functions
        ],
        extra_colors=extra_colors,
        stylesheet=stylesheet,
    )


@app.command()
def export_observations(
    projects: List[str] = typer.Option(["Kurikka GTK"]),
    kapalo_sqlite_path: Path = typer.Option(
        default=DATA_SQL_DIR_PATH,
        exists=True,
        file_okay=False,
    ),
    export_folder: Path = typer.Option(
        default="exports",
        exists=True,
        dir_okay=True,
    ),
    config_path: Path = typer.Option(default=MAPCONFIG),
):
    """
    Export kapalo tables.
    """
    exceptions, _ = read_config(config_path)

    geodataframes = export.export_projects_to_geodataframes(
        kapalo_sqlite_path=kapalo_sqlite_path,
        projects=projects,
        exceptions=exceptions,
    )

    for observation_type, geodataframe in geodataframes.items():

        dataframe_path = Path(export_folder / f"{observation_type}.csv")
        geodataframe_path = Path(export_folder / f"{observation_type}.gpkg")

        export.write_geodataframe(
            geodataframe=geodataframe,
            dataframe_path=dataframe_path,
            geodataframe_path=geodataframe_path,
        )

        assert dataframe_path.exists()
        assert geodataframe_path.exists()


def _resize_images(
    origin_dir: Path,
    destination_dir: Path,
    fixed_width: int,
    extension: str,
):
    """
    Resize images from origin_dir to destination_dir.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    for image_path in origin_dir.glob(f"*.{extension}"):
        new_path = destination_dir / image_path.name

        # From: https://www.holisticseo.digital/python-seo/resize-image/
        image = Image.open(image_path)
        width_percent = fixed_width / float(image.size[0])
        height_size = int((float(image.size[1]) * float(width_percent)))
        image = image.resize((fixed_width, height_size), Image.NEAREST)
        image.save(new_path)


@app.command()
def resize_images(
    origin_dir: Path = typer.Argument(
        DATA_IMGS_DIR_PATH, exists=True, dir_okay=True, file_okay=False
    ),
    destination_dir: Path = typer.Argument(IMGS_DIR),
    fixed_width: int = typer.Option(800),
    extension: str = typer.Option("jpg"),
):
    """
    Resize images from origin_dir to destination_dir.
    """
    _resize_images(
        origin_dir=origin_dir,
        destination_dir=destination_dir,
        fixed_width=fixed_width,
        extension=extension,
    )


@app.command()
def remote_update(
    drive: str = typer.Option("nialovdrive"),
    remote_sql_dir: str = typer.Option("kapalo/kapalo_sql"),
    remote_images_dir: str = typer.Option("kapalo/kapalo_imgs"),
    local_sql_dir: Path = typer.Option(DATA_SQL_DIR_PATH),
    local_images_dir: Path = typer.Option(DATA_IMGS_DIR_PATH),
):
    """
    Update kapalo data remotely with rclone.
    """
    try:
        subprocess.check_call(["rclone", "--help"], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        typer.secho(
            "Expected rclone to be executable on system to allow remote sync.", fg="red"
        )
        raise

    for remote, local in zip(
        (remote_sql_dir, remote_images_dir),
        (local_sql_dir, local_images_dir),
    ):
        local.mkdir(parents=True, exist_ok=True)

        cmd = (RCLONE, SYNC, f"{drive}:{remote}", str(local))
        typer.secho(f"Calling cmd: {cmd}", fg="blue")
        subprocess.check_call(cmd)
        typer.secho("Completed command!", fg="green")
