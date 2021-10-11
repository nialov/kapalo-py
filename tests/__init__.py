"""
Tests for kapalo-py.
"""

from functools import lru_cache
from itertools import cycle
from pathlib import Path

import pandas as pd

from kapalo_py import cli, utils
from kapalo_py.schema_inference import Columns

SIMPLE_HTML_FOR_MATCHING = """

    <style>html, body {width: 100%;height: 100%;margin: 0;padding: 0;}</style>
    <style>#map {position:absole;top:0;bottom:0;right:0;left:0;}</style>
    <script src="https://cdn.jsivr.net/npm/leaflet@1.6.0/dist/leaflet.js"></script>
    <script src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
    <script src="https://maxcdnootstrap/3.2.0/js/bootstrap.min.js"></script>
    <script src="https://cdnjs.me-markers/2.0.2/leaflet.awesome-markers.js"></script>
    <link rel="stylesheet" hrefdelivr.net/npm/leaflet@1.6.0/dist/leaflet.css"/>
    <link rel="stylesheet" href.com/bootstrap/3.2.0/css/bootstrap.min.css"/>
"""

ORIGIN_IMG_DIR_PATH = Path("tests/sample_data/origin_imgs")
JPG = "jpg"

STYLE_PATH = Path("tests/sample_data/styles.css")

KAPALO_SQL_DIR_PATH_PROJ_KURIKKA_GTK = Path("tests/sample_data/kapalo_sql")
KURIKKA_GTK_PROJECT = "Kurikka GTK"
DUMMY_IMG_DIR_PATH = Path("tests/sample_data/empty_imgs_dir")
DUMMY_IMG_DIR_PATH.mkdir(exist_ok=True, parents=True)


@lru_cache(maxsize=None)
def test_add_local_stylesheet_params():
    """
    Params for test_add_local_stylesheet.
    """
    return [SIMPLE_HTML_FOR_MATCHING]


@lru_cache(maxsize=None)
def test_read_kapalo_tables_params():
    """
    Params for test_read_kapalo_tables.
    """
    return [Path("tests/sample_data/kapalo_sql")]


@lru_cache(maxsize=None)
def test_gather_observation_data_params():
    """
    Params for test_gather_observation_data.
    """
    return [(Path("tests/sample_data/kapalo_sql"), dict())]


@lru_cache(maxsize=None)
def test_location_centroid_params():
    """
    Params for test_location_centroid.
    """
    return [pd.DataFrame({Columns.LATITUDE: [1, 2, 3], Columns.LONGITUDE: [1, 2, 3]})]


@lru_cache(maxsize=None)
def test_dataframe_to_markdown_params():
    """
    Params for dataframe_to_markdown.
    """
    return [pd.DataFrame({Columns.LATITUDE: [1, 2, 3], Columns.LONGITUDE: [1, 2, 3]})]


def test_observation_image_markdown_params():
    """
    Params for test_observation_image_markdown.
    """
    return test_read_kapalo_tables_params()


@lru_cache(maxsize=None)
def test_gather_project_observations_params():
    """
    Params for test_gather_project_observations.
    """
    paths = test_read_kapalo_tables_params()
    return list(zip(paths, cycle([["Kurikka GTK"]])))


@lru_cache(maxsize=None)
def test__resize_images_params():
    """
    Params for test__resize_images.
    """
    return [
        (ORIGIN_IMG_DIR_PATH, JPG),
    ]


@lru_cache(maxsize=None)
def test_webmap_compilation_params():
    """
    Params for test_webmap_compilation.
    """
    return [
        (
            KAPALO_SQL_DIR_PATH_PROJ_KURIKKA_GTK,
            DUMMY_IMG_DIR_PATH,
            [KURIKKA_GTK_PROJECT],
        )
    ]


@lru_cache(maxsize=None)
def test_apply_declination_fix_params():
    """
    Params for test_apply_declination_fix.
    """
    return [
        (358.0, 8.0, 6.0),
        (0.0, -8.0, 352.0),
        (180, 8.0, 188.0),
    ]


@lru_cache(maxsize=None)
def test_export_projects_to_geodataframes_params():
    """
    Params for test_export_projects_to_geodataframes.
    """
    return [
        (
            KAPALO_SQL_DIR_PATH_PROJ_KURIKKA_GTK,
            (KURIKKA_GTK_PROJECT,),
            utils.MapConfig(declination_value=10.0),
            False,
        )
    ]


@lru_cache(maxsize=None)
def test__setup_logging_params():
    """
    Params for test__setup_logging.
    """
    return [
        (cli.LoggingLevel.DEBUG, False),
        (cli.LoggingLevel.INFO, False),
        (cli.LoggingLevel.WARNING, False),
        (cli.LoggingLevel.ERROR, False),
        (cli.LoggingLevel.CRITICAL, False),
        (2000, True),
    ]
