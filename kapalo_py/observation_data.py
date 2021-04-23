"""
Observation data management and parsing.
"""
import logging
from dataclasses import dataclass
from kapalo_py.schema_inference import Columns, GroupTables, KapaloTables
from typing import Optional, Sequence
from pandas.core.groupby.generic import DataFrameGroupBy
import numpy as np

import pandas as pd


@dataclass
class Observation:

    """
    Observation data for map.
    """

    obs_id: str
    gdb_id: str
    latitude: float
    longitude: float
    remarks: str
    planars: pd.DataFrame = pd.DataFrame()
    linears: pd.DataFrame = pd.DataFrame()
    images: pd.DataFrame = pd.DataFrame()
    rock_observations: pd.DataFrame = pd.DataFrame()


def get_group_data(group_name: str, grouped, columns: Sequence[str]) -> pd.DataFrame:
    """
    Get group data if group_name is in grouped.
    """
    try:
        group: pd.DataFrame = grouped.get_group(group_name)
    except KeyError:
        logging.info(f"No data for {group_name}.")
        return pd.DataFrame()

    for col in columns:
        if col not in group.columns:
            raise ValueError(f"Column {col} not found in group DataFrame.")

    # Filter to wanted columns only
    df_or_srs = group.loc[:, columns] if len(columns) > 0 else group
    if not isinstance(df_or_srs, pd.DataFrame):
        wanted = pd.DataFrame(df_or_srs)
    else:
        wanted = df_or_srs

    assert isinstance(wanted, pd.DataFrame)
    return wanted


def resolve_tm_gid(tectonics: pd.DataFrame) -> Optional[str]:
    """
    Resolve tectonic measurement id.
    """
    try:
        gdb_ids = tectonics[Columns.GDB_ID].unique()
    except KeyError:
        return None
    if not len(gdb_ids) == 1:
        assert len(gdb_ids) == 0
        return None
    gdb_id: str = gdb_ids[0]

    return gdb_id


def create_observation(
    group_tables: GroupTables,
    obs_id: str,
    latitude: float,
    longitude: float,
    remarks: str,
) -> Observation:
    """
    Create Observation from data.
    """
    tectonics = get_group_data(
        group_name=obs_id, grouped=group_tables.grouped_tectonic, columns=[]
    )
    gdb_id = resolve_tm_gid(tectonics=tectonics)
    if gdb_id is None:
        return Observation(
            obs_id=obs_id, gdb_id="", latitude=latitude, longitude=longitude, remarks=""
        )

    planars = get_group_data(
        group_name=gdb_id,
        grouped=group_tables.grouped_planar,
        columns=(
            Columns.DIP,
            Columns.DIP_DIRECTION,
            Columns.STYPE_TEXT,
            Columns.FOL_TYPE_TEXT,
        ),
    )
    linears = get_group_data(
        group_name=gdb_id,
        grouped=group_tables.grouped_linear,
        columns=(Columns.DIRECTION, Columns.PLUNGE, Columns.STYPE_TEXT),
    )

    images = get_group_data(
        group_name=obs_id,
        grouped=group_tables.grouped_images,
        columns=(Columns.PICTURE_ID, Columns.REMARKS),
    )

    rock_observations = get_group_data(
        group_name=obs_id,
        grouped=group_tables.grouped_rock_obs,
        columns=(Columns.REMARKS, Columns.FIELD_NAME),
    )

    observation = Observation(
        gdb_id=gdb_id,
        obs_id=obs_id,
        planars=planars,
        linears=linears,
        images=images,
        latitude=latitude,
        longitude=longitude,
        remarks=remarks,
        rock_observations=rock_observations,
    )

    return observation
