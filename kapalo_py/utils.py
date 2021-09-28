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


def add_color(style_dict: Dict[str, str], color: Optional[str]) -> Dict[str, str]:
    """
    Add color to style dict.

    TODO: Replace with ability to specify style.
    """
    if color is None:
        assert style_dict is not None
        return style_dict
    new_dict = {}
    for key, value in style_dict.items():
        if "color" in key.lower():
            new_dict[key] = color
        else:
            new_dict[key] = value
    assert new_dict is not None
    return new_dict


def lineament_style(_, color: Optional[str] = None) -> Dict[str, str]:
    """
    Style lineament polylines.
    """
    style_dict = {
        "color": "black",
        "weight": "1",
    }
    added = add_color(style_dict, color)
    assert added is not None
    return added


def bedrock_style(_, color: Optional[str] = None) -> Dict[str, str]:
    """
    Style bedrock polygons.
    """
    style_dict = {
        "strokeColor": "blue",
        "fillOpacity": 0.0,
        "weight": 0.5,
    }
    return add_color(style_dict, color)


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
