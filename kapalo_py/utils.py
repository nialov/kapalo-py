"""
General utilities for kapalo-py.
"""

from dataclasses import dataclass
from enum import Enum, unique
from typing import Callable, Dict, Optional

import geopandas as gpd

PLANAR_TYPE = "planars"
LINEAR_TYPE = "linears"
ROCK_OBS_TYPE = "rock_observations"


def lineament_style(_):
    """
    Style lineament polylines.
    """
    return {
        "color": "black",
        "weight": "1",
    }


def bedrock_style(_):
    """
    Style bedrock polygons.
    """
    return {
        "strokeColor": "blue",
        "fillOpacity": 0.0,
        "weight": 0.5,
    }


@dataclass
class FoliumGeoJson:

    """
    Additional GeoJson data added to map.
    """

    data: gpd.GeoDataFrame
    name: str
    popup_fields: Optional[str]
    style_function: Optional[Callable[..., Dict[str, str]]]


@unique
class StyleFunctionEnum(Enum):

    """
    Enums to choose style function.
    """

    BEDROCK = bedrock_style
    LINEAMENT = lineament_style
