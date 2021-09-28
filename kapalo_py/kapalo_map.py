"""
Making spatial maps.
"""

import logging
import sqlite3
from functools import lru_cache
from itertools import chain, compress, zip_longest
from pathlib import Path
from shutil import copy
from typing import Callable, Dict, List, Sequence, Tuple

import folium
import geopandas as gpd
import markdown
import pandas as pd
from folium.plugins import locate_control

from kapalo_py import utils
from kapalo_py.observation_data import Observation, create_observation
from kapalo_py.schema_inference import Columns, GroupTables, KapaloTables, Table

# Remove static paths
KURIKKA_LINEAMENTS = Path("data/kurikka.geojson")
KURIKKA_BEDROCK = Path("data/kurikka_bedrock.geojson")


def path_copy(src: Path, dest: Path):
    """
    Copy src to dest.
    """
    if dest.exists():
        dest.unlink()
    copy(src, dest)


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


# def merge_kapalo_tables(tables: Sequence[KapaloTables]) -> KapaloTables:
#     """
#     Merge a Sequence of KapaloTables objects.
#     """
#     if not all([isinstance(val, KapaloTables) for val in tables]):
#         raise TypeError("Expected only KapaloTables objects in merge_kapalo_tables.")
#     first = tables[0]
#     if len(tables) == 1:
#         return first
#     for table in tables[1:]:
#         first = first + table
#     return first


def read_kapalo_tables(path: Path) -> List[KapaloTables]:
    """
    Read multiple kapalo.sqlite files into a list of KapaloTables.
    """
    all_tables = []
    for kapalo_sqlite_file in path.iterdir():
        assert kapalo_sqlite_file.is_file()

        # Read kapalo.sqlite
        kapalo_table = read_kapalo_table(path=kapalo_sqlite_file)
        assert isinstance(kapalo_table, KapaloTables)
        all_tables.append(kapalo_table)

    return all_tables


def read_kapalo_table(path: Path) -> KapaloTables:
    """
    Read kapalo.sqlite to create KapaloTables object.
    """
    database = sqlite3.connect(path)
    observations = sql_table_to_dataframe(Table.OBSERVATIONS.value, database)
    planar_structures = sql_table_to_dataframe(Table.PLANAR.value, database)
    tectonic_measurements = sql_table_to_dataframe(
        Table.TECTONIC_MEASUREMENTS.value, database
    )
    rock_observations_points = sql_table_to_dataframe(Table.ROCK_OBS.value, database)
    linear_structures = sql_table_to_dataframe(Table.LINEAR.value, database)
    images = sql_table_to_dataframe(Table.IMAGES.value, database)
    samples = sql_table_to_dataframe(Table.SAMPLES.value, database)
    textures = sql_table_to_dataframe(Table.TEXTURES.value, database)

    return KapaloTables(
        observations=observations,
        tectonic_measurements=tectonic_measurements,
        planar_structures=planar_structures,
        linear_structures=linear_structures,
        rock_observation_points=rock_observations_points,
        images=images,
        samples=samples,
        textures=textures,
    )


def gather_observation_data(
    kapalo_tables: KapaloTables, exceptions: Dict[str, str]
) -> List[Observation]:
    """
    Get data for observations.
    """
    group_tables = GroupTables(
        grouped_tectonic=kapalo_tables.tectonic_measurements.groupby(Columns.OBS_ID),
        grouped_planar=kapalo_tables.planar_structures.groupby(Columns.TM_GID),
        grouped_images=kapalo_tables.images.groupby(Columns.OBS_ID),
        grouped_linear=kapalo_tables.linear_structures.groupby(Columns.TM_GID),
        grouped_rock_obs=kapalo_tables.rock_observation_points.groupby(Columns.OBS_ID),
        grouped_samples=kapalo_tables.samples.groupby(Columns.OBS_ID),
        grouped_textures=kapalo_tables.textures.groupby(Columns.ROP_GID),
    )

    observations = []

    for obs_id, latitude, longitude, remarks, project in zip(
        kapalo_tables.observations[Columns.OBS_ID].values,
        kapalo_tables.observations[Columns.LATITUDE].values,
        kapalo_tables.observations[Columns.LONGITUDE].values,
        kapalo_tables.observations[Columns.REMARKS].values,
        kapalo_tables.observations[Columns.PROJECT].values,
    ):

        assert isinstance(obs_id, str)
        assert isinstance(latitude, float)
        assert isinstance(longitude, float)
        assert isinstance(remarks, str)
        assert isinstance(project, str)

        # Create an Observation
        observation = create_observation(
            group_tables=group_tables,
            obs_id=obs_id,
            latitude=latitude,
            longitude=longitude,
            remarks=remarks,
            exceptions=exceptions,
            project=project,
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


def dataframe_to_markdown(dataframe: pd.DataFrame) -> str:
    """
    Convert dataframe to html.
    """
    if dataframe.empty:
        return "\n"
    markdown_str = dataframe.to_markdown(index=False)
    if not isinstance(markdown_str, str):
        return "\n"
    markdown_str += "\n\n"
    return markdown_str


@lru_cache(maxsize=None)
def get_image_paths(path: Path) -> List[Path]:
    """
    Get jpg files at path.
    """
    img_paths = list(path.glob("*.jpg"))
    return img_paths


def observation_image_markdown(observation: Observation, imgs_path: Path) -> str:
    """
    Create markdown for images.
    """
    markdown_text_list = []
    markdown_text = "\n"
    markdown_text_list.append(markdown_text)

    if Columns.PICTURE_ID not in observation.images.columns:
        return markdown_text

    # Get all images in imgs_path
    img_paths = get_image_paths(path=imgs_path)

    # Iterate over image ids in observation
    for idx, (image_id, image_caption) in enumerate(
        zip(
            observation.images[Columns.PICTURE_ID].values,
            observation.images[Columns.REMARKS].values,
        )
    ):

        assert isinstance(image_caption, str)

        # Add linebreak
        # markdown_text += "\n"
        markdown_text_list.append("\n")

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

        # Add image markdown text to markdown_text_list
        # Example link inside markdown image:
        # <img src="http://www.google.com.au/images/nav_logo7.png">
        if idx < 2:

            # Add image and link
            markdown_text_list.append(
                f"[![{image_caption}]({match_path})]({match_path})\n\n"
            )
            markdown_text_list.append(f"*{image_caption}*")
        else:

            # Add only link text
            markdown_text_list.append(f"\n[{image_caption, image_id}]({match_path})")

    return "".join(markdown_text_list)


def observation_html(observation: Observation, imgs_path: Path) -> str:
    """
    Create html summary of observation.
    """
    markdown_text_list = []
    markdown_text_list.append(f"### {observation.obs_id}\n")

    # Tectonic measurements
    for dataframe, dataframe_label in zip(
        (
            observation.planars,
            observation.linears,
            observation.rock_observations,
            observation.samples,
            observation.textures,
        ),
        (
            "Planar Structures",
            "Linear Structures",
            "Rock Observations",
            "Samples",
            "Textures",
        ),
    ):
        markdown_text_list.append(
            f"\n#### {dataframe_label if not dataframe.empty else ''}\n\n"
        )
        markdown_text_list.append(dataframe_to_markdown(dataframe=dataframe))

    markdown_text_list.append("\n#### Observation remarks\n\n")
    markdown_text_list.append(observation.remarks)

    markdown_text_list.append(
        "\n#### Images\n\n" if not observation.images.empty else "\n"
    )
    markdown_text_list.append(
        observation_image_markdown(observation=observation, imgs_path=imgs_path)
    )

    markdown_text = "".join(markdown_text_list)

    html = markdown.markdown(markdown_text, extensions=["tables"])

    html = html.replace("src=", "height=150 src=")

    return html


def add_local_stylesheet(html: str, stylesheet: Path):
    """
    Add local stylesheet reference to html.
    """
    assert "style" in html
    if not stylesheet.exists():
        raise FileNotFoundError(f"Expected {stylesheet} to exist.")

    # compiled_re = re.compile(r"\s*<style>html")

    split_html = html.split("\n")

    matched_line_idxs = [
        idx for idx, line in enumerate(split_html) if "stylesheet" in line
    ]

    if not len(matched_line_idxs) > 0:
        raise ValueError("Expected to find style line match in html string.")

    matched_line_idx = max(matched_line_idxs) + 1

    reference = f"""    <link rel="stylesheet" href="{stylesheet.name}"/>"""

    split_html.insert(matched_line_idx, reference)

    return "\n".join(split_html)


def gather_project_observations(
    kapalo_tables: KapaloTables,
    projects: Sequence[str],
    exceptions: Dict[str, str],
) -> Tuple[List[Observation], KapaloTables]:
    """
    Gather Observations related to projects.
    """
    filtered_kapalo_tables = kapalo_tables.filter_observations_to_projects(
        projects=projects
    )

    observations = gather_observation_data(
        kapalo_tables=filtered_kapalo_tables, exceptions=exceptions
    )

    return observations, filtered_kapalo_tables


def observation_marker(
    observation: Observation, imgs_path: Path, rechecks: List[str]
) -> folium.Marker:
    """
    Make observation marker.
    """
    if not observation.linears.empty:

        # If lineation data exists plot it
        lineation_dir = observation.linears[Columns.DIRECTION].values[0]
        if not isinstance(lineation_dir, (float, int)):
            assert hasattr(lineation_dir, "item")

            # Resolve Python object from numpy
            lineation_dir = lineation_dir.item()  # type: ignore

        # Save into dict
        icon_properties = dict(
            icon="glyphicon-arrow-up",
            angle=lineation_dir,
            color=("blue" if observation.obs_id not in rechecks else "red"),
        )
    else:

        # Default icon
        icon_properties = dict(
            icon="glyphicon-stop",
            color=("lightgray" if observation.obs_id not in rechecks else "red"),
        )

    # Create folium marker
    marker = folium.Marker(
        location=[observation.latitude, observation.longitude],
        popup=folium.Popup(
            observation_html(observation=observation, imgs_path=imgs_path),
            parse_html=False,
        ),
        icon=folium.Icon(**icon_properties),
        tooltip=str(observation.obs_id),
    )

    return marker


def gather_project_observations_multiple(
    all_kapalo_tables: List[KapaloTables],
    projects: Sequence[str],
    exceptions: Dict[str, str],
) -> Tuple[List[List[Observation]], List[KapaloTables]]:
    """
    Gather all project observations from multiple KapaloTables.
    """
    all_observations = []
    all_project_tables = []
    for kapalo_tables in all_kapalo_tables:
        observations, kapalo_tables = gather_project_observations(
            kapalo_tables=kapalo_tables,
            projects=projects,
            exceptions=exceptions,
        )
        all_observations.append(observations)
        all_project_tables.append(kapalo_tables)

    return all_observations, all_project_tables


def create_project_map(
    kapalo_tables: List[KapaloTables],
    projects: List[str],
    imgs_path: Path,
    exceptions: Dict[str, str],
    rechecks: List[str],
) -> folium.Map:
    """
    Create folium map for project observations.
    """
    all_observations, all_project_tables = gather_project_observations_multiple(
        kapalo_tables, projects=projects, exceptions=exceptions
    )

    # Initialize map and center it on the observations
    # crs is EPSG3857 by default
    folium_map = folium.Map(
        location=location_centroid(
            observations=pd.concat(
                [
                    all_project_table.observations
                    for all_project_table in all_project_tables
                ]
            )
        ),
        tiles="OpenStreetMap",
    )
    observation_id_set = set()
    for observation in chain(*all_observations):
        obs_id = observation.obs_id
        if obs_id in observation_id_set:
            logging.error(f"Duplicate obs_id for {obs_id}. Skipping.")
            continue
        observation_id_set.add(obs_id)

        marker = observation_marker(
            observation=observation,
            imgs_path=imgs_path,
            rechecks=rechecks,
        )
        marker.add_to(folium_map)
    return folium_map


def resolve_extras_inputs(
    extra_datasets: List[Path],
    extra_names: List[str],
    extra_popup_fields: List[str],
    extra_style_functions: List[Callable[..., Dict[str, str]]],
) -> List[utils.FoliumGeoJson]:
    """
    Resolve extras inputs to utils.FoliumGeoJsons.
    """
    if len(extra_datasets) == 0:
        return []
    # input_lengths = [
    #     len(values)
    #     for values in (extra_names, extra_popup_fields, extra_style_functions)
    # ]
    # if any(length > 0 for length in input_lengths) and input_lengths.count(
    #     input_lengths[0]
    # ) != len(input_lengths):
    #     raise ValueError(
    #         "Expected all extras to have names, popups and style_functions."
    #     )
    extras = []
    for path, name, popup, style_function in zip_longest(
        extra_datasets,
        extra_names,
        extra_popup_fields,
        extra_style_functions,
        fillvalue=None,
    ):

        gdf = gpd.read_file(path).to_crs("EPSG:4326")
        assert isinstance(gdf, gpd.GeoDataFrame)
        folium_geojson = utils.FoliumGeoJson(
            data=gdf,
            name=name if name is not None else path.stem,
            popup_fields=popup,
            style_function=style_function
            if style_function is not None
            else style_function,
        )
        extras.append(folium_geojson)
    return extras


def webmap_compilation(
    kapalo_sqlite_path: Path,
    kapalo_imgs_path: Path,
    map_save_path: Path,
    exceptions: Dict[str, str],
    rechecks: List[str],
    projects: List[str],
    stylesheet: Path,
    extra_datasets: List[Path],
    extra_names: List[str],
    extra_popup_fields: List[str],
    extra_style_functions: List[utils.StyleFunctionEnum],
) -> folium.Map:
    """
    Compile the web map.
    """
    # Resolve if extras geodatasets are added to map
    extras = resolve_extras_inputs(
        extra_datasets=extra_datasets,
        extra_names=extra_names,
        extra_popup_fields=extra_popup_fields,
        extra_style_functions=extra_style_functions,
    )
    kapalo_tables = read_kapalo_tables(path=kapalo_sqlite_path)

    # Path to kapalo images
    imgs_path = kapalo_imgs_path

    # Create the folium map
    project_map = create_project_map(
        kapalo_tables,
        projects=projects,
        imgs_path=imgs_path,
        exceptions=exceptions,
        rechecks=rechecks,
    )

    for extra in extras:
        folium.GeoJson(
            data=extra.data,
            name=extra.name,
            style_function=extra.style_function,
            popup=(
                folium.GeoJsonPopup(fields=extra.popup_fields)
                if extra.popup_fields is not None and len(extra.popup_fields) > 0
                else None
            ),
        ).add_to(project_map)

    #     if KURIKKA_LINEAMENTS.exists() and add_extra:
    #         # Add lineaments
    #         folium.GeoJson(
    #             data="data/kurikka.geojson",
    #             name="Kurikka Lineaments",
    #             style_function=lineament_style,
    #         ).add_to(project_map)

    #     # rock_names = gpd.read_file
    # ("data/kurikka_bedrock.geojson")["ROCK_NAME_"].values

    #     if KURIKKA_BEDROCK.exists() and add_extra:
    #         # Add bedrock
    #         folium.GeoJson(
    #             data="data/kurikka_bedrock.geojson",
    #             name="Kurikka Bedrock",
    #             popup=folium.GeoJsonPopup(fields=["ROCK_NAME_"]),
    #             style_function=bedrock_style,
    #         ).add_to(project_map)

    # Add user location control
    locate_control.LocateControl(
        locateOptions={"enableHighAccuracy": True, "watch": True, "timeout": 100000}
    ).add_to(project_map)

    # Save map to live-mapping repository
    project_map.save(str(map_save_path))

    # Replace image paths to local
    # replaced_img_paths_html = map_save_path.read_text().replace(
    #     "data/kapalo_imgs", "kapalo_imgs"
    # )
    replaced_img_paths_html = map_save_path.read_text().replace(
        str(kapalo_imgs_path), kapalo_imgs_path.name
    )

    styled_html = add_local_stylesheet(
        html=replaced_img_paths_html, stylesheet=stylesheet
    )

    map_save_path.write_text(styled_html)

    # # Remove old
    # rmtree(map_imgs_path)

    # # Copy over images
    # copytree(kapalo_imgs_path, map_imgs_path)

    # Copy css to local map project
    path_copy(stylesheet, map_save_path.parent / "styles.css")

    return project_map
