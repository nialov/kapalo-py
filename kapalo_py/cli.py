"""
Command line integration.
"""
import logging
import subprocess
from enum import Enum, unique
from pathlib import Path
from typing import List, Optional

import typer
from PIL import Image, UnidentifiedImageError

from kapalo_py import export, kapalo_map, utils
from kapalo_py.logger import setup_module_logging

APP = typer.Typer()


# rclone command arguments
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


@unique
class LoggingLevel(Enum):

    """
    Enums for logging levels.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _setup_logging(logging_level: LoggingLevel):
    """
    Set up logging from command-line options.
    """
    logging_level_int = getattr(logging, logging_level.value, None)
    if not isinstance(logging_level_int, int):
        raise TypeError(
            f"Expected logging_level to be an attribute of logging. Got: {logging_level}."
        )
    setup_module_logging(logging_level_int=logging_level_int)


@APP.callback()
def setup_logging(
    logging_level: LoggingLevel = typer.Option(LoggingLevel.WARNING.value),
):
    """
    Kapalo data extraction and processing.
    """
    _setup_logging(logging_level=logging_level)


@APP.command()
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
    projects: List[str] = typer.Option(
        [], help="Indicate project identifiers to extract from kapalo sqlite files."
    ),
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
    kapalo_map.webmap_compilation(
        kapalo_sqlite_path=kapalo_sqlite_path,
        kapalo_imgs_path=kapalo_imgs_path,
        map_save_path=map_save_path,
        config_path=config_path,
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


@APP.command()
def export_observations(
    projects: List[str] = typer.Option(["Kurikka GTK"]),
    kapalo_sqlite_path: Path = typer.Option(
        default=DATA_SQL_DIR_PATH,
        exists=True,
        file_okay=False,
        help="Directory containing kapalo sqlite files. Files must end with '.sqlite'.",
    ),
    export_folder: Path = typer.Option(
        default="exports",
        dir_okay=True,
    ),
    config_path: Optional[Path] = typer.Option(default=MAPCONFIG),
):
    """
    Export kapalo tables.
    """
    geodataframes = export.export_projects_to_geodataframes(
        kapalo_sqlite_path=kapalo_sqlite_path,
        projects=projects,
        config_path=config_path,
    )

    export.write_geodataframes(geodataframes=geodataframes, export_folder=export_folder)


def _resize_images(
    origin_dir: Path,
    destination_dir: Path,
    fixed_width: int,
    extension: str,
    overwrite: bool,
):
    """
    Resize images from origin_dir to destination_dir.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    for image_path in origin_dir.glob(f"*.{extension}"):
        new_path = destination_dir / image_path.name
        if new_path.exists() and not overwrite:
            logging.info("Found existing converted image and overwrite is False.")
            continue

        # From: https://www.holisticseo.digital/python-seo/resize-image/
        try:
            image = Image.open(image_path)
        except UnidentifiedImageError:
            logging.error(f"Expected {image_path} to be a valid image.", exc_info=True)
            continue
        width_percent = fixed_width / float(image.size[0])
        height_size = int((float(image.size[1]) * float(width_percent)))
        image = image.resize((fixed_width, height_size), Image.NEAREST)
        image.save(new_path)


@APP.command()
def resize_images(
    origin_dir: Path = typer.Argument(
        DATA_IMGS_DIR_PATH, exists=True, dir_okay=True, file_okay=False
    ),
    destination_dir: Path = typer.Argument(IMGS_DIR),
    fixed_width: int = typer.Option(800),
    extension: str = typer.Option("jpg"),
    overwrite: bool = typer.Option(False),
):
    """
    Resize images from origin_dir to destination_dir.
    """
    _resize_images(
        origin_dir=origin_dir,
        destination_dir=destination_dir,
        fixed_width=fixed_width,
        extension=extension,
        overwrite=overwrite,
    )


@APP.command()
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
