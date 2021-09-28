"""
Tests for kapalo_map.py.
"""

from pathlib import Path

import folium
import pytest

import tests
from kapalo_py import kapalo_map, utils
from kapalo_py.observation_data import Observation
from kapalo_py.schema_inference import KapaloTables


@pytest.mark.parametrize("style_path", [tests.STYLE_PATH])
@pytest.mark.parametrize("html_str", tests.test_add_local_stylesheet_params())
def test_add_local_stylesheet(html_str, style_path):
    """
    Test add_local_stylesheet.
    """
    assert style_path.exists()
    assert "style" in html_str
    assert isinstance(html_str, str)
    result = kapalo_map.add_local_stylesheet(html_str, stylesheet=style_path)

    assert isinstance(result, str)
    assert style_path.name in result

    assert len(result) > len(html_str)


@pytest.mark.parametrize("path", tests.test_read_kapalo_tables_params())
def test_read_kapalo_tables(path: Path):
    """
    Test read_kapalo_tables.
    """
    assert path.is_dir()
    result = kapalo_map.read_kapalo_tables(path)
    assert isinstance(result, list)
    assert len(result) == len(list(path.iterdir()))

    if len(result) != 0:
        assert isinstance(result[0], KapaloTables)
        assert not result[0].observations.empty

    return result


@pytest.mark.parametrize("path,exceptions", tests.test_gather_observation_data_params())
def test_gather_observation_data(path, exceptions):
    """
    Test gather_observation_data.
    """
    kapalo_tables = test_read_kapalo_tables(path)
    result = kapalo_map.gather_observation_data(kapalo_tables[0], exceptions=exceptions)

    assert isinstance(result, list)
    assert isinstance(result[0], Observation)
    assert isinstance(result[0].obs_id, str)


@pytest.mark.parametrize("observations", tests.test_location_centroid_params())
def test_location_centroid(observations):
    """
    Test location_centroid.
    """
    result = kapalo_map.location_centroid(observations)
    assert isinstance(result, tuple)
    assert all(isinstance(val, float) for val in result)


@pytest.mark.parametrize("dataframe", tests.test_dataframe_to_markdown_params())
def test_dataframe_to_markdown(dataframe):
    """
    Test dataframe_to_markdown.
    """
    result = kapalo_map.dataframe_to_markdown(dataframe)
    assert isinstance(result, str)


def test_get_image_paths(fix_images: Path):
    """
    Test get_image_paths.
    """
    assert isinstance(fix_images, Path)
    result = kapalo_map.get_image_paths(fix_images)
    assert len(result) == 5


def test_observation_image_markdown(fix_observations, fix_images):
    """
    Test observation_image_markdown.
    """
    observations = fix_observations

    for observation in observations:
        result = kapalo_map.observation_image_markdown(observation, fix_images)

        assert isinstance(result, str)
        assert len(result) > 0


def test_observation_html(fix_observations, fix_images):
    """
    Test observation_html.
    """
    observations = fix_observations

    for observation in observations:
        result = kapalo_map.observation_html(observation, fix_images)

        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.parametrize(
    "path,projects", tests.test_gather_project_observations_params()
)
def test_gather_project_observations(path, projects):
    """
    Test gather_project_observations.
    """
    assert isinstance(projects, list)
    assert isinstance(projects[0], str)
    kapalo_tables = kapalo_map.read_kapalo_tables(path)
    result = kapalo_map.gather_project_observations(kapalo_tables[0], projects, dict())

    assert isinstance(result, tuple)
    assert isinstance(result[0], list)
    assert isinstance(result[1], KapaloTables)
    assert isinstance(result[0][0], Observation)


def test_observation_marker(fix_observations, fix_images):
    """
    Test observation_marker.
    """
    for observation in fix_observations:
        result = kapalo_map.observation_marker(
            observation, imgs_path=fix_images, rechecks=[]
        )
        assert isinstance(result, folium.Marker)


@pytest.mark.parametrize(
    "path,projects", tests.test_gather_project_observations_params()
)
def test_gather_project_observations_multiple(path, projects):
    """
    Test gather_project_observations_multiple.
    """
    kapalo_tables = kapalo_map.read_kapalo_tables(path)
    result = kapalo_map.gather_project_observations_multiple(
        all_kapalo_tables=kapalo_tables, projects=projects, exceptions=dict()
    )
    assert isinstance(result, tuple)
    assert isinstance(result[0], list)
    assert isinstance(result[1], list)


@pytest.mark.parametrize(
    "path,projects", tests.test_gather_project_observations_params()
)
def test_create_project_map(path, projects, fix_images):
    """
    Test create_project_map.
    """
    kapalo_tables = kapalo_map.read_kapalo_tables(path)
    result = kapalo_map.create_project_map(
        kapalo_tables=kapalo_tables,
        projects=projects,
        exceptions=dict(),
        imgs_path=fix_images,
        rechecks=[],
    )
    assert isinstance(result, folium.Map)


params = (
    "extra_datasets,extra_names,extra_popup_fields,"
    "extra_style_functions,extra_colors"
)


@pytest.mark.parametrize(
    params,
    [
        ([], [], [], [], []),
        (
            [Path("tests/sample_data/sample_lineaments.geojson")],
            ["Sample Lineaments"],
            [""],
            [utils.StyleFunctionEnum.LINEAMENT],
            ["black"],
        ),
        (
            [Path("tests/sample_data/sample_lineaments.geojson")] * 2,
            ["Sample Lineaments"] * 2,
            [],
            [],
            ["black"] * 2,
        ),
        (
            [Path("tests/sample_data/sample_lineaments.geojson")],
            [],
            [],
            [],
            [],
        ),
    ],
)
@pytest.mark.parametrize(
    "sqlite_path,imgs_path,projects",
    tests.test_webmap_compilation_params(),
)
def test_webmap_compilation(
    sqlite_path,
    imgs_path,
    projects,
    extra_datasets,
    extra_names,
    extra_popup_fields,
    extra_style_functions,
    extra_colors,
    tmp_path,
):
    """
    Test webmap_compilation.
    """
    for extra_input in (
        extra_datasets,
        extra_names,
        extra_popup_fields,
        extra_style_functions,
    ):
        assert isinstance(extra_input, list)
    map_save_path = tmp_path / "index.html"

    result = kapalo_map.webmap_compilation(
        kapalo_sqlite_path=sqlite_path,
        kapalo_imgs_path=imgs_path,
        exceptions=dict(),
        rechecks=[],
        stylesheet=tests.STYLE_PATH,
        extra_datasets=extra_datasets,
        extra_names=extra_names,
        extra_popup_fields=extra_popup_fields,
        extra_style_functions=extra_style_functions,
        extra_colors=extra_colors,
        projects=projects,
        map_save_path=map_save_path,
    )

    assert map_save_path.exists()
    map_html = map_save_path.read_text()
    assert len(map_html) > 0

    assert isinstance(result, folium.Map)
