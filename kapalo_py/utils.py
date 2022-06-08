"""
General utilities for kapalo-py.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Callable, Dict, Optional, Tuple

import geopandas as gpd
import numpy as np

# Attributes of Observation class
# TODO: Handle better.
PLANAR_TYPE = "planars"
LINEAR_TYPE = "linears"
ROCK_OBS_TYPE = "rock_observations"
IMAGES_TYPE = "images"
SAMPLES_TYPE = "samples"
TEXTURES_TYPE = "textures"


@dataclass
class MapConfig:

    """
    Configuration from mapconfig.ini.
    """

    rechecks: Tuple[str, ...] = ()
    exceptions: Dict[str, str] = field(default_factory=dict)
    declination_value: float = 0.0
    projects: Tuple[str, ...] = ()
    bounds: Optional[Tuple[float, float, float, float]] = None
    bounds_epsg: Optional[int] = None


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

    BEDROCK = "Bedrock"
    LINEAMENT = "Lineament"

    @classmethod
    def style_function(cls, enum) -> Callable:
        """
        Choose function based on enum.
        """
        styles = {cls.BEDROCK: bedrock_style, cls.LINEAMENT: lineament_style}
        chosen = styles[enum]
        assert callable(chosen)
        return chosen


def apply_declination_fix(azimuth, declination_value: float) -> float:
    """
    Apply declination fix to azimuth value.

    Returns values in range [0, 360].
    """
    azimuth = float(azimuth)
    invalid_azimuth = (
        not isinstance(azimuth, float)
        or np.isnan(azimuth)
        or not (0.0 <= azimuth <= 360.0)
    )
    invalid_declination_value = (
        not isinstance(declination_value, float)
        or np.isnan(declination_value)
        or not (-360.0 <= declination_value <= 360.0)
    )

    if invalid_azimuth or invalid_declination_value:

        fault = (
            f"Could not apply declination fix for azimuth {azimuth}"
            f" with declination_value {declination_value} due to "
        )

        if invalid_azimuth and invalid_declination_value:
            logging.error(fault + "both being invalid.")
        elif invalid_azimuth:
            logging.error(fault + "invalid azimuth.")
        elif invalid_declination_value:
            logging.error(fault + "invalid declination_value.")
        else:
            raise ValueError("Undefined result.")
        return azimuth

    added = azimuth + declination_value
    if added > 360.0:
        added = added - 360.0
    if added < 0.0:
        added = 360 + added
    return added
