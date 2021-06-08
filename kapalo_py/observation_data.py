"""
Observation data management and parsing.
"""
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import pandas as pd

from kapalo_py.schema_inference import Columns, GroupTables


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
    project: str
    planars: pd.DataFrame = pd.DataFrame()
    linears: pd.DataFrame = pd.DataFrame()
    images: pd.DataFrame = pd.DataFrame()
    rock_observations: pd.DataFrame = pd.DataFrame()
    samples: pd.DataFrame = pd.DataFrame()


def get_group_data(
    group_name: str,
    grouped,
    columns: Sequence[str],
    exceptions: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Get group data if group_name is in grouped.
    """
    if exceptions is None:
        exceptions = dict()
    group_name = group_name if group_name not in exceptions else exceptions[group_name]
    try:
        group: pd.DataFrame = grouped.get_group(group_name)
    except KeyError:
        logging.info("No data for {}.".format(group_name))
        return pd.DataFrame()

    for col in columns:
        if col not in group.columns:
            print(group.columns)
            raise ValueError(
                f"Column {col} not found in group DataFrame columns:."
                f"\n{group.columns}"
            )

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
    if len(gdb_ids) != 1:
        if len(gdb_ids) != 0:
            logging.error(
                f"Expected one tectonic measurement id per observation.\n"
                f"Found {len(gdb_ids)} which were {list(gdb_ids)}. Choosing last."
            )
            return gdb_ids[-1]
        return None
    gdb_id: str = gdb_ids[0]

    return gdb_id


def create_observation(
    group_tables: GroupTables,
    obs_id: str,
    latitude: float,
    longitude: float,
    remarks: str,
    project: str,
    exceptions: Dict[str, str],
) -> Observation:
    """
    Create Observation from data.
    """
    tectonics = get_group_data(
        group_name=obs_id,
        grouped=group_tables.grouped_tectonic,
        columns=[],
        exceptions=exceptions,
    )
    gdb_id = resolve_tm_gid(tectonics=tectonics)
    if gdb_id is None:
        planars = pd.DataFrame()
        linears = pd.DataFrame()
        gdb_id = ""

    else:
        planars = get_group_data(
            group_name=gdb_id,
            grouped=group_tables.grouped_planar,
            columns=(
                Columns.DIP,
                Columns.DIP_DIRECTION,
                Columns.STYPE_TEXT,
                Columns.FOL_TYPE_TEXT,
                Columns.STYPE,
            ),
        )
        linears = get_group_data(
            group_name=gdb_id,
            grouped=group_tables.grouped_linear,
            columns=(
                Columns.DIRECTION,
                Columns.PLUNGE,
                Columns.STYPE_TEXT,
                Columns.STYPE,
            ),
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
    samples = get_group_data(
        group_name=obs_id,
        grouped=group_tables.grouped_samples,
        columns=[Columns.SAMPLE_ID, Columns.FIELD_NAME],
        exceptions=exceptions,
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
        samples=samples,
        project=project,
    )

    return observation
