"""
Utilities for exporting kapalo data.
"""

import logging
from itertools import chain
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from kapalo_py import filter_rules, kapalo_map, schema_inference, utils
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
    config_path: Optional[Path],
) -> Dict[str, gpd.GeoDataFrame]:
    """
    Export kapalo projects to folder.
    """
    map_config = kapalo_map.read_config(config_path=config_path)
    logging.info(
        "Reading sqlite files.",
        extra=dict(
            kapalo_sqlite_path=kapalo_sqlite_path,
        ),
    )
    # TODO: Remove code duplication with webmap_compilation func
    logging.info(
        "Adding projects from config file to project targets (if specified).",
        extra=dict(config_projects=map_config.projects, cli_projects=projects),
    )

    all_projects = list(set([*projects, *map_config.projects]))
    kapalo_tables = kapalo_map.read_kapalo_tables(path=kapalo_sqlite_path)

    logging.info(
        "Gathering project observations from projects.", extra=dict(projects=projects)
    )
    (all_observations, _,) = kapalo_map.gather_project_observations_multiple(
        kapalo_tables,
        projects=all_projects,
        exceptions=map_config.exceptions,
        bounds=map_config.bounds,
        bounds_epsg=map_config.bounds_epsg,
    )

    observations_flat = list(chain(*all_observations))
    if len(observations_flat) == 0:
        logging.warning("No Observations gathered/found.")
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

        logging.info(
            "Compiling dataframe from observation_type",
            extra=dict(
                observation_type=observation_type,
            ),
        )
        geodataframe = compile_type_dataframe(
            observations=observations, observation_type=observation_type
        )

        points: List[Point] = [
            point
            for point in geodataframe["geometry"].values
            if isinstance(point, Point)
        ]

        logging.debug("Asserting that all geometries are points.")
        assert len(points) == geodataframe.shape[0]

        logging.info("Adding x, y and z columns.")
        geodataframe["x"] = [point.x for point in points]
        geodataframe["y"] = [point.y for point in points]
        geodataframe["z"] = [0.0 for _ in points]

        logging.info(
            "Performing declination fix on direction columns.",
            extra=dict(
                declination_value=declination_value,
            ),
        )
        for column in schema_inference.AZIMUTH_COLUMNS:
            if column in geodataframe.columns:
                logging.info(
                    "Applying declination fix to column.",
                    extra=dict(column=column, declination_value=declination_value),
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


def filter_invalid_rows(
    geodataframe: gpd.GeoDataFrame,
    columns: Dict[str, Callable[..., bool]],
) -> gpd.GeoDataFrame:
    """
    Filter invalid rows from GeoDataFrame.
    """
    for col, validator in columns.items():
        assert isinstance(col, str)
        assert isinstance(validator, Callable)
        len_before = geodataframe.shape[0]
        try:
            geodataframe = geodataframe.loc[geodataframe[col].apply(validator)]
        except Exception:
            logging.error(
                "Failed to filter geodataframe rows.",
                exc_info=True,
                extra=dict(col=col, geodataframe_columns=geodataframe.columns),
            )
        len_after = geodataframe.shape[0]
        logging.info(
            "Filtering out column data.",
            extra=dict(
                col=col,
                len_before=len_before,
                len_after=len_after,
                difference=(len_before - len_after),
            ),
        )

    return geodataframe


def filter_observation_type_geodataframe(
    observation_type: str, geodataframe: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Filter observation_type geodataframe.

    Has filter rules for **some** observation types, not all.
    """
    if geodataframe.empty:
        return geodataframe
    if observation_type == utils.PLANAR_TYPE:
        return filter_invalid_rows(
            geodataframe=geodataframe,
            columns={
                Columns.DIP: filter_rules.filter_dip,
                Columns.DIP_DIRECTION: filter_rules.filter_dip_dir,
            },
        )
    if observation_type == utils.LINEAR_TYPE:
        return filter_invalid_rows(
            geodataframe=geodataframe,
            columns={
                Columns.PLUNGE: filter_rules.filter_dip,
                Columns.DIRECTION: filter_rules.filter_dip_dir,
            },
        )
    return geodataframe


def check_for_empty_geodataframe(geodataframe: gpd.GeoDataFrame) -> bool:
    """
    Check if geodataframe is empty.
    """
    return geodataframe.empty or geodataframe.shape[0] == 0


def write_geodataframes(
    geodataframes: Dict[str, gpd.GeoDataFrame], export_folder: Path
):
    """
    Write GeoDataFrame datasets to export_folder.
    """
    logging.info("Creating export directory", extra=dict(export_folder=export_folder))
    export_folder.mkdir(exist_ok=True)
    for observation_type, geodataframe in geodataframes.items():

        len_before = geodataframe.shape[0]
        geodataframe = filter_observation_type_geodataframe(
            geodataframe=geodataframe, observation_type=observation_type
        )
        len_after = geodataframe.shape[0]
        logging.info(
            "Filtered data in geodataframe.",
            extra=dict(
                observation_type=observation_type,
                len_before=len_before,
                len_after=len_after,
                difference=len_before - len_after,
            ),
        )
        assert len_before >= len_after

        if check_for_empty_geodataframe(geodataframe=geodataframe):
            logging.warning(
                "Empty geodataframe for observation_type",
                extra=dict(
                    observation_type=observation_type,
                    len_before_filter=len_before,
                    len_after_filter=len_after,
                ),
            )
            continue

        dataframe_path = Path(export_folder / f"{observation_type}.csv")
        geodataframe_path = Path(export_folder / f"{observation_type}.gpkg")

        logging.info(
            "Saving (Geo)DataFrames.",
            extra=dict(
                dataframe_path=dataframe_path,
                geodataframe_path=geodataframe_path,
            ),
        )
        write_geodataframe(
            geodataframe=geodataframe,
            dataframe_path=dataframe_path,
            geodataframe_path=geodataframe_path,
        )

        assert dataframe_path.exists()
        assert geodataframe_path.exists()
