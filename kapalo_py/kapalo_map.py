"""
Making spatial maps.
"""

import configparser
import logging
import sqlite3
from functools import lru_cache, partial
from itertools import chain, compress, zip_longest
from pathlib import Path
from shutil import copy
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import folium
import geopandas as gpd
import markdown
import numpy as np
import pandas as pd
from folium.plugins import locate_control

from kapalo_py import utils
from kapalo_py.observation_data import Observation, create_observation
from kapalo_py.schema_inference import Columns, GroupTables, KapaloTables, Table

STYLES_CSS = "styles.css"

# mapconfig.ini headers
EXCEPTIONS = "exceptions"
RECHECK = "recheck"
PROJECTS = "projects"
DECLINATION = "declination"
DECLINATION_VALUE = "declination_value"
BOUNDS = "bounds"
EPSG = "epsg"
XMIN = "xmin"
XMAX = "xmax"
YMIN = "ymin"
YMAX = "ymax"


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


def sql_table_to_dataframe(table: str, connection: sqlite3.Connection) -> pd.DataFrame:
    """
    Read sqlite table to DataFrame.
    """
    dataframe = pd.read_sql_query(sql=f"SELECT * FROM {table};", con=connection)  # noqa
    assert isinstance(dataframe, pd.DataFrame)
    return dataframe


def read_kapalo_tables(path: Path) -> List[KapaloTables]:
    """
    Read multiple kapalo.sqlite files into a list of KapaloTables.
    """
    path_exists = path.exists()
    path_is_file = path.is_file()

    if not path_exists or path_is_file:
        logging.error(
            "Cannot read kapalo tables as path doesn't exist.",
            extra=dict(path_exists=path_exists, path_is_file=path_is_file, path=path),
        )
        return []
    all_tables = []
    for kapalo_sqlite_file in path.glob("*.sqlite"):
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
    mean_latitude = observations[Columns.LATITUDE].dropna().mean()
    mean_longitude = observations[Columns.LONGITUDE].dropna().mean()
    assert isinstance(mean_latitude, float)
    assert isinstance(mean_longitude, float)
    assert not np.isnan(mean_latitude)
    assert not np.isnan(mean_longitude)
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
    assert isinstance(markdown_str, str)
    return markdown_str


@lru_cache(maxsize=None)
def get_image_paths(path: Path) -> List[Path]:
    """
    Get jpg files at path.
    """
    img_paths = list(path.glob("*.jpg"))
    return img_paths


def observation_image_markdown(
    observation: Observation, imgs_path: Optional[Path]
) -> str:
    """
    Create markdown for images.
    """
    markdown_text_list = []
    markdown_text = "\n"
    markdown_text_list.append(markdown_text)

    if Columns.PICTURE_ID not in observation.images.columns or imgs_path is None:
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

        # assert types
        assert isinstance(image_caption, str)
        assert isinstance(image_id, str)

        # Add linebreak
        # markdown_text += "\n"
        markdown_text_list.append("\n")

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
                f"[![{image_caption}]({match_path})]({match_path})\n"
            )
            # markdown_text_list.append(f"*{image_caption}*")
        else:

            # Add only link text
            link_text = f"{image_id}: {image_caption}"
            markdown_text_list.append(f"\n[{link_text}]({match_path})")

    if not all(isinstance(part, str) for part in markdown_text_list):
        logging.error(
            "Expected only str members in markdown_text_list."
            f" Unique types: {set(map(type, markdown_text_list))}. Converting."
        )
        markdown_text_list = [str(value) for value in markdown_text_list]
    return "".join(markdown_text_list)


def observation_html(observation: Observation, imgs_path: Optional[Path]) -> str:
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
        if dataframe.empty:
            logging.info(f"DataFrame for {dataframe_label} was empty.")
            continue
        if Columns.REMARKS in dataframe.columns:
            logging.info(
                f"Removing column {Columns.REMARKS} from dataframe"
                f" {dataframe_label} inplace before adding to map markdown."
            )
            dataframe.drop(columns=[Columns.REMARKS], inplace=True)
        markdown_text_list.append(f"\n#### {dataframe_label}\n\n")
        markdown_text_list.append(dataframe_to_markdown(dataframe=dataframe))

    markdown_text_list.append("\n#### Observation remarks\n\n")
    markdown_text_list.append(str(observation.remarks))

    markdown_text_list.append(
        "\n#### Images\n\n" if not observation.images.empty else "\n"
    )
    markdown_text_list.append(
        observation_image_markdown(observation=observation, imgs_path=imgs_path)
    )

    if not all(isinstance(value, str) for value in markdown_text_list):
        unexpected_type = set(map(type, markdown_text_list)).remove(str)
        logging.error(
            f"Unexpected non-str type {unexpected_type} in markdown_text_list."
            " Converting to str."
        )
        markdown_text_list = list(map(str, markdown_text_list))

    markdown_text = "".join(markdown_text_list)

    html = markdown.markdown(markdown_text, extensions=["tables", "markdown_captions"])

    html = html.replace("src=", "height=150 src=")
    assert isinstance(html, str)

    return html


def add_local_stylesheet(html: str, stylesheet: Path):
    """
    Add local stylesheet reference to html string.
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
    bounds: Optional[Tuple[float, float, float, float]],
    bounds_epsg: Optional[int],
) -> Tuple[List[Observation], KapaloTables]:
    """
    Gather Observations related to projects.
    """
    filtered_kapalo_tables = kapalo_tables.filter_observations_to_projects(
        projects=projects
    )

    # Filter extracted observations to minx, miny, maxx, maxy bounds
    if bounds is not None and bounds_epsg is not None:
        logging.info(
            "Filtering observations to bounds.",
            extra=dict(bounds=bounds, bounds_epsg=bounds_epsg),
        )
        filtered_kapalo_tables = filtered_kapalo_tables.filter_observations_to_bounds(
            bounds=bounds, epsg=bounds_epsg
        )

    # Convert to Observation instances for easier handling (than dataframes)
    observations = gather_observation_data(
        kapalo_tables=filtered_kapalo_tables, exceptions=exceptions
    )

    return observations, filtered_kapalo_tables


def observation_marker(
    observation: Observation, imgs_path: Optional[Path], rechecks: Tuple[str, ...]
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
    bounds: Optional[Tuple[float, float, float, float]],
    bounds_epsg: Optional[int],
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
            bounds=bounds,
            bounds_epsg=bounds_epsg,
        )
        all_observations.append(observations)
        all_project_tables.append(kapalo_tables)

    return all_observations, all_project_tables


def add_observations_to_map(
    observations: List[Observation],
    folium_map: folium.Map,
    imgs_path: Optional[Path],
    rechecks: Tuple[str, ...] = (),
) -> folium.Map:
    """
    Add observations to folium map as folium markers.
    """
    observation_id_set = set()
    for observation in chain(observations):
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


def create_project_map(
    kapalo_tables: List[KapaloTables],
    projects: List[str],
    imgs_path: Path,
    map_config: utils.MapConfig,
) -> folium.Map:
    """
    Create folium map for project observations.
    """
    all_observations, all_project_tables = gather_project_observations_multiple(
        kapalo_tables,
        projects=projects,
        exceptions=map_config.exceptions,
        bounds=map_config.bounds,
        bounds_epsg=map_config.bounds_epsg,
    )

    logging.info("Initializing map and centering it on the observations.")
    logging.debug("folium.Map crs is EPSG3857 by default.")
    folium_map = folium.Map(
        location=location_centroid(
            observations=pd.concat(
                [
                    all_project_table.observations
                    for all_project_table in all_project_tables
                ],
                ignore_index=True,
            )
        ),
        tiles="OpenStreetMap",
    )

    folium_map = add_observations_to_map(
        observations=list(chain(*all_observations)),
        folium_map=folium_map,
        imgs_path=imgs_path,
        rechecks=map_config.rechecks,
    )
    return folium_map


def resolve_extras_inputs(
    extra_datasets: List[Path],
    extra_names: List[str],
    extra_popup_fields: List[str],
    extra_style_functions: List[Callable[..., Dict[str, str]]],
    extra_colors: List[str],
) -> List[utils.FoliumGeoJson]:
    """
    Resolve extras inputs to utils.FoliumGeoJsons.
    """
    if len(extra_datasets) == 0:
        return []
    extras = []
    for path, name, popup, style_function, color in zip_longest(
        extra_datasets,
        extra_names,
        extra_popup_fields,
        extra_style_functions,
        extra_colors,
        fillvalue=None,
    ):

        gdf = gpd.read_file(path).to_crs("EPSG:4326")
        assert isinstance(gdf, gpd.GeoDataFrame)
        if style_function is not None:
            if not callable(style_function):
                raise TypeError(f"Expected {style_function} to be callable.")

        # Create partial function with color filled
        style_function_with_color = (
            partial(style_function, color=color) if style_function is not None else None
        )

        # Create FoliumGeoJson instance with all required information
        # for adding the geodataset to folium map
        folium_geojson = utils.FoliumGeoJson(
            data=gdf,
            name=name if name is not None else path.stem,
            popup_fields=popup,
            style_function=style_function_with_color,
        )
        logging.info(f"Created FoliumGeoJson instance {folium_geojson}.")
        extras.append(folium_geojson)
    return extras


def webmap_compilation(
    kapalo_sqlite_path: Path,
    kapalo_imgs_path: Path,
    map_save_path: Path,
    projects: List[str],
    stylesheet: Path,
    extra_datasets: List[Path],
    extra_names: List[str],
    extra_colors: List[str],
    extra_popup_fields: List[str],
    extra_style_functions: List[Callable[..., Dict[str, str]]],
    config_path: Optional[Path] = None,
) -> folium.Map:
    """
    Compile the web map.
    """
    logging.info(
        "Reading map config ini file.",
        extra=dict(config_path=config_path),
    )
    map_config = read_config(config_path=config_path)
    logging.info(
        "Adding projects from config file to project targets (if specified).",
        extra=dict(config_projects=map_config.projects, cli_projects=projects),
    )

    all_projects = list(set([*projects, *map_config.projects]))
    assert len(all_projects) >= len(projects)
    assert len(all_projects) >= len(map_config.projects)
    logging.info(
        "Reading sqlite tables into DataFrames and parsing into KapaloTables",
        extra=dict(kapalo_sqlite_path=kapalo_sqlite_path),
    )
    kapalo_tables = read_kapalo_tables(path=kapalo_sqlite_path)

    logging.info(
        "Creating the folium map.",
        extra=dict(
            kapalo_tables_len=len(kapalo_tables),
            projects=all_projects,
            imgs_path=kapalo_imgs_path,
            map_config=map_config,
        ),
    )
    project_map = create_project_map(
        kapalo_tables,
        projects=all_projects,
        imgs_path=kapalo_imgs_path,
        map_config=map_config,
    )

    project_map = add_extra_map_content(
        project_map,
        extra_datasets=extra_datasets,
        extra_names=extra_names,
        extra_colors=extra_colors,
        extra_popup_fields=extra_popup_fields,
        extra_style_functions=extra_style_functions,
    )

    logging.info(
        "Writing and styling folium.Map.",
        extra=dict(
            map_save_path=map_save_path,
            kapalo_imgs_path=kapalo_imgs_path,
            stylesheet=stylesheet,
            stylesheet_exists=stylesheet.exists(),
        ),
    )
    project_map = write_and_style_html_map(
        project_map=project_map,
        map_save_path=map_save_path,
        kapalo_imgs_path=kapalo_imgs_path,
        stylesheet=stylesheet,
    )

    return project_map


def write_and_style_html_map(
    project_map: folium.Map,
    map_save_path: Path,
    kapalo_imgs_path: Path,
    stylesheet: Path,
) -> folium.Map:
    """
    Write folium.Map to html file and consequently edit the html in the file.

    The edit adds reference to a stylesheet (styles.css).
    """
    # Save map to live-mapping repository
    project_map.save(str(map_save_path))

    replaced_img_paths_html = map_save_path.read_text().replace(
        str(kapalo_imgs_path), kapalo_imgs_path.name
    )

    styled_html = add_local_stylesheet(
        html=replaced_img_paths_html, stylesheet=stylesheet
    )

    map_save_path.write_text(styled_html)

    # Copy css to local map project
    path_copy(stylesheet, map_save_path.parent / STYLES_CSS)

    return project_map


def add_extra_map_content(
    project_map: folium.Map,
    extra_datasets: List[Path],
    extra_names: List[str],
    extra_colors: List[str],
    extra_popup_fields: List[str],
    extra_style_functions: List[Callable[..., Dict[str, str]]],
):
    """
    Add optional extra content to map.
    """
    # Resolve if extras geodatasets are added to map
    extras = resolve_extras_inputs(
        extra_datasets=extra_datasets,
        extra_names=extra_names,
        extra_popup_fields=extra_popup_fields,
        extra_style_functions=extra_style_functions,
        extra_colors=extra_colors,
    )

    for extra in extras:
        if extra.style_function is not None:
            is_correct = callable(extra.style_function) and isinstance(
                extra.style_function(None), dict
            )
            if not is_correct:
                raise TypeError(
                    f"Expected {extra.style_function} to be callable and "
                    f"return dict: {extra.style_function(None)}"
                )
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

    # Add user location control
    locate_control.LocateControl(
        locateOptions={"enableHighAccuracy": True, "watch": True, "timeout": 100000}
    ).add_to(project_map)

    return project_map


def read_config(config_path: Optional[Path]) -> utils.MapConfig:
    """
    Read mapconfig.ini if it exists.
    """
    logging.info(
        "Reading config.",
        extra=dict(
            config_path_absolute=config_path
            if config_path is None
            else config_path.absolute()
        ),
    )
    if (config_path is None) or (not config_path.exists()):
        return utils.MapConfig()

    config_parser = configparser.ConfigParser(allow_no_value=True)
    # Overwrite reading keys as lowercase
    config_parser.optionxform = lambda option: option
    config_parser.read(config_path)
    rechecks = tuple(config_parser[RECHECK].keys()) if RECHECK in config_parser else ()
    exceptions = (
        dict(config_parser[EXCEPTIONS].items())
        if EXCEPTIONS in config_parser
        else dict()
    )
    declination_value = (
        float(dict(config_parser[DECLINATION].items())[DECLINATION_VALUE])
        if DECLINATION in config_parser
        else 0.0
    )
    config_projects = (
        tuple(config_parser[PROJECTS].keys()) if PROJECTS in config_parser else ()
    )

    # No quotes allowed in actual project string
    config_projects = tuple(
        [proj.replace('"', "").replace("'", "") for proj in config_projects]
    )

    bounds_section = config_parser[BOUNDS] if BOUNDS in config_parser else None
    bounds = None
    epsg = None
    if bounds_section is not None:
        try:
            xmin = float(bounds_section[XMIN])
            xmax = float(bounds_section[XMAX])
            ymin = float(bounds_section[YMIN])
            ymax = float(bounds_section[YMAX])
            epsg = int(bounds_section[EPSG])
            bounds = (xmin, ymin, xmax, ymax)
        except Exception:
            logging.error(
                "Failed to parse bounds section",
                extra=dict(bounds_section=bounds_section),
            )

    return utils.MapConfig(
        rechecks=rechecks,
        exceptions=exceptions,
        declination_value=declination_value,
        projects=config_projects,
        bounds=bounds,
        bounds_epsg=epsg,
    )
