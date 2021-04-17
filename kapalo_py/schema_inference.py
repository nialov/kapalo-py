"""
Documentation of schema links.
"""

from enum import Enum, unique
from collections import OrderedDict


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


connections = [
    {Table.OBSERVATIONS: "OBSID", Table.TECTONIC_MEASUREMENTS: "OBSID"},
    {Table.TECTONIC_MEASUREMENTS: "GDB_ID", Table.PLANAR: "TM_GID"},
    {Table.TECTONIC_MEASUREMENTS: "GDB_ID", Table.LINEAR: "TM_GID"},
    {Table.IMAGES: "OBSID", Table.OBSERVATIONS: "OBSID"},
]
