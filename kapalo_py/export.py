"""
Utilities for exporting kapalo data.
"""

from itertools import chain
from pathlib import Path
from typing import Dict, List, Sequence

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

import kapalo_py.kapalo_map as kapalo_map
from kapalo_py.observation_data import Observation
from kapalo_py.schema_inference import Columns


def compile_type_dataframe(
    observations: List[Observation], observation_type: str
) -> gpd.GeoDataFrame:
    """
    Create DataFrame of type observations.

    type is linear or planar.
    """
    type_observations = []

    for observation in observations:

        # Make copy of planar DataFrame
        type_df: pd.DataFrame = getattr(observation, observation_type).copy()

        # Add column with observation jds
        type_df[Columns.OBS_ID] = observation.obs_id

        # Add column with remarks
        type_df[Columns.REMARKS] = observation.remarks

        # Add column with project
        type_df[Columns.PROJECT] = observation.project

        # Add column with Point geometry
        type_df[Columns.GEOMETRY] = Point(observation.longitude, observation.latitude)

        type_observations.append(type_df)

    dataframe = pd.concat(type_observations)

    assert isinstance(dataframe, pd.DataFrame)

    geodataframe = gpd.GeoDataFrame(dataframe, crs="EPSG:4326").to_crs("EPSG:3067")

    assert isinstance(geodataframe, gpd.GeoDataFrame)

    return geodataframe


def export_projects_to_folder(
    kapalo_sqlite_path: Path,
    export_folder: Path,
    projects: Sequence[str],
    exceptions: Dict[str, str],
):
    """
    Export kapalo projects to folder.
    """
    # Read kapalo.sqlite
    kapalo_tables = kapalo_map.read_kapalo_tables(path=kapalo_sqlite_path)

    (all_observations, _,) = kapalo_map.gather_project_observations_multiple(
        kapalo_tables, projects=projects, exceptions=exceptions
    )

    observations_flat = list(chain(*all_observations))
    if len(observations_flat) == 0:
        print("No Observations gathered/found.")
        return
    # Iterate over chosen observation types
    for observation_type in ("planars", "linears"):

        geodataframe = compile_type_dataframe(
            observations=observations_flat, observation_type=observation_type
        )

        dataframe_path = Path(export_folder / f"{observation_type}.csv")
        geodataframe_path = Path(export_folder / f"{observation_type}.gpkg")

        points: List[Point] = [
            point
            for point in geodataframe["geometry"].values
            if isinstance(point, Point)
        ]

        assert len(points) == geodataframe.shape[0]

        geodataframe["x"] = [point.x for point in points]
        geodataframe["y"] = [point.y for point in points]

        geodataframe.drop(columns=["geometry"]).to_csv(dataframe_path)
        geodataframe.to_file(geodataframe_path, driver="GPKG")
        geodataframe.to_file(
            geodataframe_path.with_suffix(".shp"), driver="ESRI Shapefile"
        )
