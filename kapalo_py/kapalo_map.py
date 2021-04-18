"""
Making spatial maps.
"""

import folium
import pandas as pd
from typing import List, Tuple
from pathlib import Path
from kapalo_py.schema_inference import Columns, Table, KapaloTables, GroupTables
from kapalo_py.observation_data import Observation, create_observation
import sqlite3
import markdown


def dip_colors(dip: float):
    """
    Color dip values.
    """
    color = "blue"
    if dip > 60:
        color = "red"
    elif dip > 30:
        color = "green"
    return color


def sql_table_to_dataframe(table: str, connection: sqlite3.Connection):
    """
    Read sqlite table to DataFrame.
    """
    dataframe = pd.read_sql_query(sql=f"SELECT * FROM {table};", con=connection)
    assert isinstance(dataframe, pd.DataFrame)
    return dataframe


def read_kapalo_tables(path: Path) -> KapaloTables:
    """
    Read kapalo.sqlite for KapaloTables.
    """
    db = sqlite3.connect(path)
    observations = sql_table_to_dataframe(Table.OBSERVATIONS.value, db)
    planar_structures = sql_table_to_dataframe(Table.PLANAR.value, db)
    tectonic_measurements = sql_table_to_dataframe(
        Table.TECTONIC_MEASUREMENTS.value, db
    )
    rock_observations_points = sql_table_to_dataframe(Table.ROCK_OBS.value, db)
    linear_structures = sql_table_to_dataframe(Table.LINEAR.value, db)
    images = sql_table_to_dataframe(Table.IMAGES.value, db)

    return KapaloTables(
        observations=observations,
        tectonic_measurements=tectonic_measurements,
        planar_structures=planar_structures,
        linear_structures=linear_structures,
        rock_observation_points=rock_observations_points,
        images=images,
    )


def gather_observation_data(kapalo_tables: KapaloTables) -> List[Observation]:
    """
    Get data for observations.
    """
    grouped_tectonic = kapalo_tables.tectonic_measurements.groupby(Columns.OBS_ID)
    grouped_planar = kapalo_tables.planar_structures.groupby(Columns.TM_GID)
    grouped_linear = kapalo_tables.linear_structures.groupby(Columns.TM_GID)
    grouped_images = kapalo_tables.images.groupby(Columns.OBS_ID)

    group_tables = GroupTables(
        grouped_tectonic=grouped_tectonic,
        grouped_planar=grouped_planar,
        grouped_images=grouped_images,
        grouped_linear=grouped_linear,
    )

    observations = []

    for obs_id, latitude, longitude in zip(
        kapalo_tables.observations[Columns.OBS_ID].values,
        kapalo_tables.observations[Columns.LATITUDE].values,
        kapalo_tables.observations[Columns.LONGITUDE].values,
    ):

        assert isinstance(obs_id, str)
        assert isinstance(latitude, float)
        assert isinstance(longitude, float)

        observation = create_observation(
            group_tables=group_tables,
            obs_id=obs_id,
            latitude=latitude,
            longitude=longitude,
        )

        observations.append(observation)
    return observations


def location_centroid(observations: pd.DataFrame) -> Tuple[float, float]:
    """
    Get mean location for project.
    """
    mean_latitude = observations[Columns.LATITUDE].mean()
    mean_longitude = observations[Columns.LONGITUDE].mean()
    assert isinstance(mean_latitude, float)
    assert isinstance(mean_longitude, float)
    return mean_latitude, mean_longitude


# def dataframe_to_html(dataframe: pd.DataFrame) -> str:
#     """
#     Convert dataframe to html.
#     """
#     if dataframe.empty:
#         return "\n"
#     html = dataframe.to_html()
#     if not isinstance(html, str):
#         return "\n"
#     html += "\n"
#     return html


def dataframe_to_markdown(dataframe: pd.DataFrame) -> str:
    """
    Convert dataframe to html.
    """
    if dataframe.empty:
        return "\n"
    markdown_str = dataframe.to_markdown(index=False)
    if not isinstance(markdown_str, str):
        return "\n"
    markdown_str += "\n"
    return markdown_str


def observation_html(observation: Observation):
    """
    Create html summary of observation.
    """
    markdown_text = f"### {observation.obs_id}\n"

    for dataframe in (observation.planars, observation.linears):
        markdown_text += dataframe_to_markdown(dataframe=dataframe)

    html = markdown.markdown(markdown_text, extensions=["tables"])
    return html


def create_project_map(kapalo_tables: KapaloTables, project: str):
    """
    Create folium map for project observations.
    """
    kapalo_tables.filter_observations_to_project(project=project)

    observations = gather_observation_data(kapalo_tables=kapalo_tables)

    map = folium.Map(
        location=location_centroid(observations=kapalo_tables.observations),
        tiles="OpenStreetMap",
    )
    for observation in observations:
        # dip = row["DIP"]
        # dip_dir = row["DIRECTION_OF_DIP"]
        # rotation = dip_dir - 90 if dip_dir > 90 else 270 + dip_dir
        # rock_name = row["ROCK_NAME_TEXT"]
        # measurement = f"{dip_dir:>3}/{dip:>2}".replace(" ", "0")
        folium.Marker(
            location=[observation.latitude, observation.longitude],
            popup=folium.Popup(
                observation_html(observation=observation), parse_html=False
            ),
            icon=folium.Icon(
                icon="glyphicon-chevron-right",
            ),
            tooltip=str(observation.obs_id),
        ).add_to(map)
    return map
