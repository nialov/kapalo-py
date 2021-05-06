"""
Documentation of schema links.
"""

from enum import Enum, unique
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from pandas.core.groupby.generic import DataFrameGroupBy
from typing import Sequence


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

    def __post_init__(self):
        """
        Validate all DataFrames.
        """
        assert all(
            [
                isinstance(df, pd.DataFrame)
                for df in (
                    self.observations,
                    self.tectonic_measurements,
                    self.planar_structures,
                    self.linear_structures,
                    self.rock_observation_points,
                    self.images,
                )
            ]
        )

    def copy(self):
        """
        Make copy of self.
        """
        self_as_dict = {key: item.copy() for key, item in asdict(self).items()}

        return KapaloTables(**self_as_dict)

    def filter_observations_to_projects(self, projects: Sequence[str]):
        """
        Filter observations table to project(s).
        """

        self_copy = self.copy()

        self_copy.observations = self.observations.loc[
            np.isin(self.observations[Columns.PROJECT], projects)
        ]

        return self_copy


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


# connections = [
#     {Table.OBSERVATIONS: Columns.OBS_ID, Table.TECTONIC_MEASUREMENTS: Columns.OBS_ID},
#     {Table.TECTONIC_MEASUREMENTS: Columns.GDB_ID, Table.PLANAR: Columns.TM_GID},
#     {Table.TECTONIC_MEASUREMENTS: Columns.GDB_ID, Table.LINEAR: Columns.TM_GID},
#     {Table.IMAGES: Columns.OBS_ID, Table.OBSERVATIONS: Columns.OBS_ID},
#     {Table.ROCK_OBS: Columns.OBS_ID, Table.OBSERVATIONS: Columns.OBS_ID},
# ]
