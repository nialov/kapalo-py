"""
Documentation of schema links.
"""

from dataclasses import asdict, dataclass, fields
from enum import Enum, unique
from itertools import chain
from typing import Sequence, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import pandera as pa
from pandas.core.groupby.generic import DataFrameGroupBy
from shapely.geometry import Point, box


class Columns:

    """
    Column names in tables.
    """

    OBS_ID = "OBSID"
    GDB_ID = "GDB_ID"
    TM_GID = "TM_GID"
    DIP = "DIP"
    DIP_DIRECTION = "DIRECTION_OF_DIP"
    DIRECTION = "DIRECTION"
    PLUNGE = "PLUNGE"
    PICTURE_ID = "PICTURE_ID"
    PROJECT = "PROJECT"
    LATITUDE = "LAT"
    LONGITUDE = "LON"
    REMARKS = "REMARKS"
    STYPE_TEXT = "STYPE_TEXT"
    FOL_TYPE_TEXT = "FOL_TYPE_TEXT"
    FIELD_NAME = "FIELD_NAME"
    GEOMETRY = "geometry"
    SAMPLE_ID = "SAMPLEID"
    FOL_TYPE = "F_TYPE"
    STYPE = "STYPE"
    ROCK_NAME = "ROCK_NAME"
    ROP_GID = "ROP_GID"
    ST_1 = "ST_1"
    ST_2 = "ST_2"
    H_SENCE = "H_SENCE"
    H_SENCE_TEXT = "H_SENCE_TEXT"

    # Not a column in sqlite schema
    # Made for image dataframe exporting
    OBSERVATION_REMARKS = "OBS_REMARKS"


AZIMUTH_COLUMNS = (Columns.DIP_DIRECTION, Columns.DIRECTION)

PLANAR_COLUMNS = (
    Columns.REMARKS,
    Columns.DIP,
    Columns.DIP_DIRECTION,
    Columns.STYPE_TEXT,
    Columns.FOL_TYPE_TEXT,
    Columns.STYPE,
    Columns.H_SENCE,
    Columns.H_SENCE_TEXT,
)
LINEAR_COLUMNS = (
    Columns.REMARKS,
    Columns.DIRECTION,
    Columns.PLUNGE,
    Columns.STYPE_TEXT,
    Columns.STYPE,
)

IMAGE_COLUMNS = (Columns.PICTURE_ID, Columns.REMARKS)
SAMPLES_COLUMNS = (Columns.SAMPLE_ID, Columns.FIELD_NAME)
ROCK_OBSERVATIONS_COLUMNS_INITIAL = (
    Columns.REMARKS,
    Columns.FIELD_NAME,
    Columns.ROCK_NAME,
    Columns.GDB_ID,
)
ROCK_OBSERVATIONS_COLUMNS_FINAL = tuple(
    col for col in ROCK_OBSERVATIONS_COLUMNS_INITIAL if col not in (Columns.GDB_ID,)
)
TEXTURE_COLUMNS = (Columns.ST_2, Columns.ST_1)


@unique
class Table(Enum):

    """
    kapalo.sqlite column names as enums.
    """

    OBSERVATIONS = "Observation"
    PLANAR = "BFDS_Planar_structure"
    TECTONIC_MEASUREMENTS = "Tectonic_measurement"
    ROCK_OBS = "Rock_observation_point"
    LINEAR = "BFDS_Linear_structure"
    IMAGES = "Outcrop_picture"
    SAMPLES = "Sample"
    TEXTURES = "BFDS_SaT"


@dataclass
class KapaloTables:

    """
    kapalo.sqlite table collection.
    """

    observations: pd.DataFrame
    tectonic_measurements: pd.DataFrame
    planar_structures: pd.DataFrame
    linear_structures: pd.DataFrame
    rock_observation_points: pd.DataFrame
    images: pd.DataFrame
    samples: pd.DataFrame
    textures: pd.DataFrame

    def __post_init__(self):
        """
        Validate all DataFrames.
        """
        assert all(
            isinstance(df, pd.DataFrame)
            for df in (
                self.observations,
                self.tectonic_measurements,
                self.planar_structures,
                self.linear_structures,
                self.rock_observation_points,
                self.images,
                self.samples,
                self.textures,
            )
        )

    def copy(self):
        """
        Make copy of self.
        """
        self_as_dict = {key: item.copy() for key, item in asdict(self).items()}

        return KapaloTables(**self_as_dict)

    def filter_observations_to_projects(
        self, projects: Sequence[str]
    ) -> "KapaloTables":
        """
        Filter observations table to project(s).
        """
        self_copy = self.copy()

        self_copy.observations = self.observations.loc[
            np.isin(self.observations[Columns.PROJECT], projects)
        ]

        return self_copy

    def filter_observations_to_bounds(
        self, bounds: Tuple[float, float, float, float], epsg: int
    ) -> "KapaloTables":
        """
        Filter observations table to bounds.
        """
        self_copy = self.copy()

        points = [
            Point(x, y)
            for x, y in zip(
                self.observations[Columns.LONGITUDE],
                self.observations[Columns.LATITUDE],
            )
        ]
        points_geoseries = gpd.GeoSeries(points, crs="EPSG:4326")
        points_geoseries_transformed = points_geoseries.to_crs(epsg=epsg)
        bounds_polygon = box(*bounds)
        self_copy.observations = self.observations.loc[
            [
                point.intersects(bounds_polygon)
                for point in points_geoseries_transformed.geometry.values
            ]
        ]

        return self_copy

    def __add__(self, other):
        """
        Implement merging multiple KapaloTables objects.
        """
        if not isinstance(other, KapaloTables):
            raise TypeError("Expected other to be an instance of KapaloTables.")
        # First check if all observation ids are unique.
        all_obs_ids = np.array(
            list(
                chain(
                    self.observations[Columns.OBS_ID].values,
                    other.observations[Columns.OBS_ID].values,
                )
            )
        )

        # Get unique values and counts of occurrence
        # count is 1 if unique
        values, counts = np.unique(all_obs_ids, return_counts=True)

        non_unique = values[counts != 1]
        if len(non_unique) != 0:
            return ValueError(
                f"Expected all unique observation ids.\nNon-unique: {non_unique}"
            )

        new_attributes = dict()
        # Can now "safely" merge
        for field in fields(self):
            attribute = field.name
            assert hasattr(self, attribute)
            assert hasattr(other, attribute)

            new_df = pd.concat(
                [getattr(self, attribute), getattr(other, attribute)], ignore_index=True
            )
            new_attributes[attribute] = new_df

        return KapaloTables(**new_attributes)

    def __radd__(self, other):
        """
        Right side add.
        """
        return self.__add__(other)


@dataclass
class GroupTables:

    """
    Grouped DataFrames.
    """

    grouped_tectonic: DataFrameGroupBy
    grouped_planar: DataFrameGroupBy
    grouped_linear: DataFrameGroupBy
    grouped_images: DataFrameGroupBy
    grouped_rock_obs: DataFrameGroupBy
    grouped_samples: DataFrameGroupBy
    grouped_textures: DataFrameGroupBy


def default_schema_from_columns(columns: Tuple[str, ...]):
    """
    Create default schema for just column names.
    """
    schema = pa.DataFrameSchema(
        columns={col: pa.Column(required=True, nullable=True) for col in columns}
    )
    return schema


PLANARS_SCHEMA = default_schema_from_columns(columns=PLANAR_COLUMNS)
LINEARS_SCHEMA = default_schema_from_columns(columns=LINEAR_COLUMNS)
IMAGE_SCHEMA = default_schema_from_columns(columns=IMAGE_COLUMNS)
ROCK_OBSERVATIONS_SCHEMA = default_schema_from_columns(
    columns=ROCK_OBSERVATIONS_COLUMNS_FINAL
)
SAMPLES_SCHEMA = default_schema_from_columns(columns=SAMPLES_COLUMNS)
TEXTURES_SCHEMA = default_schema_from_columns(columns=TEXTURE_COLUMNS)
