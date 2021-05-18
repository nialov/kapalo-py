"""
Documentation of schema links.
"""

from enum import Enum, unique
import numpy as np
import pandas as pd
from itertools import chain
from dataclasses import dataclass, asdict, fields
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


# connections = [
#     {Table.OBSERVATIONS: Columns.OBS_ID, Table.TECTONIC_MEASUREMENTS: Columns.OBS_ID},
#     {Table.TECTONIC_MEASUREMENTS: Columns.GDB_ID, Table.PLANAR: Columns.TM_GID},
#     {Table.TECTONIC_MEASUREMENTS: Columns.GDB_ID, Table.LINEAR: Columns.TM_GID},
#     {Table.IMAGES: Columns.OBS_ID, Table.OBSERVATIONS: Columns.OBS_ID},
#     {Table.ROCK_OBS: Columns.OBS_ID, Table.OBSERVATIONS: Columns.OBS_ID},
# ]
