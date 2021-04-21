"""
Making spatial maps.
"""

import logging
import folium
from itertools import compress
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

    for obs_id, latitude, longitude, remarks in zip(
        kapalo_tables.observations[Columns.OBS_ID].values,
        kapalo_tables.observations[Columns.LATITUDE].values,
        kapalo_tables.observations[Columns.LONGITUDE].values,
        kapalo_tables.observations[Columns.REMARKS].values,
    ):

        assert isinstance(obs_id, str)
        assert isinstance(latitude, float)
        assert isinstance(longitude, float)
        assert isinstance(remarks, str)

        observation = create_observation(
            group_tables=group_tables,
            obs_id=obs_id,
            latitude=latitude,
            longitude=longitude,
            remarks=remarks,
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


def observation_image_markdown(observation: Observation, imgs_path: Path) -> str:
    """
    Create markdown for images.
    """
    markdown_text = "\n"

    if Columns.PICTURE_ID not in observation.images.columns:
        return markdown_text

    # Get all images in imgs_path
    # TODO: Do not get img paths multiple times
    img_paths = list(imgs_path.glob("*.jpg"))

    # Iterate over image ids in observation
    for idx, (image_id, image_caption) in enumerate(
        zip(
            observation.images[Columns.PICTURE_ID].values,
            observation.images[Columns.REMARKS].values,
        )
    ):

        assert isinstance(image_caption, str)

        # Add linebreak
        markdown_text += "\n"

        # assert type
        assert isinstance(image_id, str)

        # Get boolean list of matches
        matches = [image_id in img_path.stem for img_path in img_paths]

        # Report no matches
        if sum(matches) != 1:
            logging.error(f"No match for image id {image_id} in {imgs_path}")
            return "\n"

        # Only one match exists, compress img_paths to that match path
        match: List[Path] = list(compress(img_paths, matches))
        assert len(match) == 1
        match_path = match[0]
        # One image match, correct

        # Add image markdown text to markdown_text
        # Example link inside markdown image:
        # <img src="http://www.google.com.au/images/nav_logo7.png">
        if idx < 2:
            markdown_text += f"[![{image_caption}]({match_path})]({match_path})"
            markdown_text += image_caption
        else:
            markdown_text += f"[{image_caption, image_id}]({match_path})"

    return markdown_text


def observation_html(observation: Observation, imgs_path: Path):
    """
    Create html summary of observation.
    """
    markdown_text = f"### {observation.obs_id}\n"

    # Tectonic measurements
    for dataframe in (observation.planars, observation.linears):
        markdown_text += "\n"
        markdown_text += dataframe_to_markdown(dataframe=dataframe)

    markdown_text += observation.remarks

    markdown_text += observation_image_markdown(
        observation=observation, imgs_path=imgs_path
    )

    html = markdown.markdown(markdown_text, extensions=["tables"])

    html = html.replace("src=", "height=150 src=")
    return html


def create_project_map(kapalo_tables: KapaloTables, project: str, imgs_path: Path):
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
        lineation_dir = (
            observation.linears[Columns.DIRECTION].values[0]
            if not observation.linears.empty
            else 0.0
        )
        if not isinstance(lineation_dir, (float, int)):
            assert hasattr(lineation_dir, "item")
            lineation_dir = lineation_dir.item()  # type: ignore
        folium.Marker(
            location=[observation.latitude, observation.longitude],
            popup=folium.Popup(
                observation_html(observation=observation, imgs_path=imgs_path),
                parse_html=False,
            ),
            icon=folium.Icon(
                icon="glyphicon-arrow-up",
                angle=lineation_dir,
            ),
            tooltip=str(observation.obs_id),
        ).add_to(map)
    return map
