"""
Utilities for exporting kapalo data.
"""

from kapalo_py.schema_inference import Columns
from kapalo_py.observation_data import Observation
import kapalo_py.kapalo_map as kapalo_map
from pathlib import Path
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from typing import List, Tuple, Sequence


def compile_type_dataframes(
    observations: List[Observation], observation_type: str
) -> Tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Create DataFrame of type observations.
    """
    type_observations = []

    for observation in observations:

        # Make copy of planar DataFrame
        type_df: pd.DataFrame = getattr(observation, observation_type).copy()

        # Add column with observation jds
        type_df[Columns.OBS_ID] = observation.obs_id

        # Add column with remarks
        type_df[Columns.REMARKS] = observation.remarks

        # Add column with Point geometry
        type_df[Columns.GEOMETRY] = Point(observation.longitude, observation.latitude)

        type_observations.append(type_df)

    dataframe = pd.concat(type_observations)

    assert isinstance(dataframe, pd.DataFrame)

    geodataframe = gpd.GeoDataFrame(dataframe, crs="EPSG:4326").to_crs("EPSG:3067")

    assert isinstance(geodataframe, gpd.GeoDataFrame)

    return dataframe, geodataframe


def export_projects_to_folder(
    kapalo_sqlite_path: Path,
    export_folder: Path,
    projects: Sequence[str],
):
    """
    Compile the web map.
    """
    # Read kapalo.sqlite
    kapalo_tables = kapalo_map.read_kapalo_tables(path=kapalo_sqlite_path)

    # Gather observations
    observations = kapalo_map.gather_project_observations(
        kapalo_tables=kapalo_tables,
        projects=projects,
    )

    # Iterate over chosen observation types
    for observation_type in ("planars", "linears"):

        assert hasattr(observations[0], observation_type)

        dataframe, geodataframe = compile_type_dataframes(
            observations=observations, observation_type=observation_type
        )

        dataframe_path = Path(export_folder / f"{observation_type}.csv")
        geodataframe_path = Path(export_folder / f"{observation_type}.gpkg")

        dataframe.to_csv(dataframe_path)
        geodataframe.to_file(geodataframe_path, driver="GPKG")
