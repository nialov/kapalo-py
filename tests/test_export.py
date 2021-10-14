"""
Tests for export.py.
"""

from pathlib import Path

import pytest

import tests
from kapalo_py import export, schema_inference, utils


@pytest.mark.parametrize(
    "kapalo_sqlite_path,projects,map_config,is_empty",
    tests.test_export_projects_to_geodataframes_params(),
)
def test_export_projects_to_geodataframes(
    kapalo_sqlite_path, projects, map_config, is_empty: bool
):
    """
    Test export_projects_to_geodataframes.
    """
    result = export.export_projects_to_geodataframes(
        kapalo_sqlite_path, projects, map_config
    )
    assert isinstance(result, dict)

    if not is_empty:
        assert len(result) > 0

    default_map_config = utils.MapConfig()

    default_result = export.export_projects_to_geodataframes(
        kapalo_sqlite_path, projects, default_map_config
    )

    for result_gdf, default_gdf in zip(result.values(), default_result.values()):
        assert result_gdf.shape[0] == default_gdf.shape[0]

        for col in schema_inference.AZIMUTH_COLUMNS:
            if col in result_gdf:
                # Some might be same due to invalid values!
                amount_same = sum(result_gdf[col] == default_gdf[col])
                # But in this case there's less than 1 % invalid values
                assert amount_same < result_gdf.shape[0] * 0.01


@pytest.mark.parametrize("geodataframes", tests.test_write_geodataframes_params())
def test_write_geodataframes(geodataframes, tmp_path: Path):
    """
    Test write_geodataframes.
    """
    assert isinstance(geodataframes, dict)
    assert tmp_path.exists()
    assert tmp_path.is_dir()
    export.write_geodataframes(geodataframes, export_folder=tmp_path)
