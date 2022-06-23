"""
Tests for export.py.
"""

from pathlib import Path

import geopandas as gpd
import pytest

import tests
from kapalo_py import export, schema_inference, utils


@pytest.mark.parametrize(
    "kapalo_sqlite_path,projects,config_path,is_empty",
    tests.test_export_projects_to_geodataframes_params(),
)
def test_export_projects_to_geodataframes(
    kapalo_sqlite_path, projects, config_path, is_empty: bool, data_regression
):
    """
    Test export_projects_to_geodataframes.
    """
    result = export.export_projects_to_geodataframes(
        kapalo_sqlite_path, projects, config_path=config_path
    )
    assert isinstance(result, dict)

    if is_empty:
        assert len(result) == 0
        return

    if not is_empty:
        assert len(result) > 0

    # Check that export table length does not change
    data_regression.check(dict(result_length=len(result)))

    default_result = export.export_projects_to_geodataframes(
        kapalo_sqlite_path, projects, None
    )

    for result_gdf, default_gdf in zip(result.values(), default_result.values()):
        assert isinstance(result_gdf, gpd.GeoDataFrame)
        assert isinstance(default_gdf, gpd.GeoDataFrame)
        assert result_gdf.shape[0] == default_gdf.shape[0]

        for col in schema_inference.AZIMUTH_COLUMNS:
            if col in result_gdf:
                # Some might be same due to invalid values!
                amount_same = sum(result_gdf[col] == default_gdf[col])
                # But in this case there's less than 1 % invalid values
                assert amount_same < result_gdf.shape[0] * 0.01

    # Test that horizontal fault sense is in dataframe
    planars_gdf = result[utils.PLANAR_TYPE]
    assert schema_inference.Columns.H_SENCE in planars_gdf.columns
    assert schema_inference.Columns.H_SENCE_TEXT in planars_gdf.columns
    assert len(planars_gdf[schema_inference.Columns.H_SENCE_TEXT].unique()) > 1
    assert len(planars_gdf[schema_inference.Columns.H_SENCE].unique()) > 1

    # Test that both image and observation remarks remain in image dataframe
    images_gdf = result[utils.IMAGES_TYPE]
    assert schema_inference.Columns.OBSERVATION_REMARKS in images_gdf.columns
    assert schema_inference.Columns.REMARKS in images_gdf.columns


@pytest.mark.parametrize("geodataframes", tests.test_write_geodataframes_params())
def test_write_geodataframes(geodataframes, tmp_path: Path):
    """
    Test write_geodataframes.
    """
    assert isinstance(geodataframes, dict)
    assert tmp_path.exists()
    assert tmp_path.is_dir()
    export.write_geodataframes(geodataframes, export_folder=tmp_path)
