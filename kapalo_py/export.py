"""
Utilities for exporting kapalo data.
"""

from itertools import chain
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from structlog import get_logger

from kapalo_py import kapalo_map, schema_inference, utils
from kapalo_py.observation_data import Observation
from kapalo_py.schema_inference import Columns

logger = get_logger()


def compile_type_dataframe(
    observations: List[Observation], observation_type: str
) -> gpd.GeoDataFrame:
    """
    Create DataFrame of type observations.

    type is linear or planar.
    """
    type_observations = []

    for observation in observations:

        # Make copy of DataFrame
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

    dataframe = pd.concat(type_observations, ignore_index=True)

    assert isinstance(dataframe, pd.DataFrame)

    # Coordinates in dataframe are in 4326 but are transformed to 3067
    geodataframe = gpd.GeoDataFrame(dataframe, crs="EPSG:4326").to_crs("EPSG:3067")

    assert isinstance(geodataframe, gpd.GeoDataFrame)

    return geodataframe


def write_geodataframe(
    geodataframe: gpd.GeoDataFrame, dataframe_path: Path, geodataframe_path: Path
):
    """
    Write geodataframe to folder as csv, shapefile and geopackage.
    """
    geodataframe.drop(columns=["geometry"]).to_csv(dataframe_path)
    geodataframe.to_file(geodataframe_path, driver="GPKG")
    geodataframe.to_file(geodataframe_path.with_suffix(".shp"), driver="ESRI Shapefile")


def export_projects_to_geodataframes(
    kapalo_sqlite_path: Path,
    projects: Sequence[str],
    map_config: utils.MapConfig,
) -> Dict[str, gpd.GeoDataFrame]:
    """
    Export kapalo projects to folder.
    """
    logger.info("Reading sqlite files.", kapalo_sqlite_path=kapalo_sqlite_path)
    kapalo_tables = kapalo_map.read_kapalo_tables(path=kapalo_sqlite_path)

    logger.info(f"Gathering project observations from projects: {projects}.")
    (all_observations, _,) = kapalo_map.gather_project_observations_multiple(
        kapalo_tables, projects=projects, exceptions=map_config.exceptions
    )

    observations_flat = list(chain(*all_observations))
    if len(observations_flat) == 0:
        logger.warning("No Observations gathered/found.")
        return dict()

    return compile_type_dataframes(
        observations=observations_flat, declination_value=map_config.declination_value
    )


def compile_type_dataframes(
    observations: List[Observation],
    declination_value: float,
    observation_types: Tuple[str, ...] = (
        utils.PLANAR_TYPE,
        utils.LINEAR_TYPE,
        utils.ROCK_OBS_TYPE,
        utils.IMAGES_TYPE,
        utils.SAMPLES_TYPE,
        utils.TEXTURES_TYPE,
    ),
) -> Dict[str, gpd.GeoDataFrame]:
    """
    Create dataframes of observation type from observations.

    E.g. planar, linear or rock observations.

    Applies declination fix based on given value.
    """
    geodataframes: Dict[str, gpd.GeoDataFrame] = dict()
    # Iterate over chosen observation types
    for observation_type in observation_types:

        logger.info(
            "Compiling dataframe from observation_type",
            observation_type=observation_type,
        )
        geodataframe = compile_type_dataframe(
            observations=observations, observation_type=observation_type
        )

        points: List[Point] = [
            point
            for point in geodataframe["geometry"].values
            if isinstance(point, Point)
        ]

        logger.debug("Asserting that all geometries are points.")
        assert len(points) == geodataframe.shape[0]

        logger.info("Adding x and y columns.")
        geodataframe["x"] = [point.x for point in points]
        geodataframe["y"] = [point.y for point in points]

        logger.info(
            "Performing declination fix on direction columns.",
            declination_value=declination_value,
        )
        for column in schema_inference.AZIMUTH_COLUMNS:
            if column in geodataframe.columns:
                logger.info(
                    f"Applying declination fix to column: {column} with"
                    f" declination_value of {declination_value}."
                )
                column_values = geodataframe[column]
                assert column_values is not None
                geodataframe[column] = [
                    utils.apply_declination_fix(
                        azimuth=azimuth, declination_value=declination_value
                    )
                    for azimuth in column_values.values
                ]

        geodataframes[observation_type] = geodataframe

    return geodataframes


def write_geodataframes(
    geodataframes: Dict[str, gpd.GeoDataFrame], export_folder: Path
):
    """
    Write GeoDataFrame datasets to export_folder.
    """
    logger.info("Creating export directory", export_folder=export_folder)
    export_folder.mkdir(exist_ok=True)
    for observation_type, geodataframe in geodataframes.items():

        if geodataframe.empty or geodataframe.shape[0] == 0:
            logger.warning(
                "Empty geodataframe for observation_type",
                observation_type=observation_type,
            )
            continue

        dataframe_path = Path(export_folder / f"{observation_type}.csv")
        geodataframe_path = Path(export_folder / f"{observation_type}.gpkg")

        logger.info(
            "Saving (Geo)DataFrames.",
            dataframe_path=dataframe_path,
            geodataframe_path=geodataframe_path,
        )
        write_geodataframe(
            geodataframe=geodataframe,
            dataframe_path=dataframe_path,
            geodataframe_path=geodataframe_path,
        )

        assert dataframe_path.exists()
        assert geodataframe_path.exists()
