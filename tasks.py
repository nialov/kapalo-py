"""
Invoke tasks.

Most tasks employ nox to create a virtual session for testing.
"""
from invoke import task
from pathlib import Path
from time import strftime
from itertools import chain
import re
from shutil import copy


PACKAGE_NAME = "kapalo_py"
CITATION_CFF_PATH = Path("CITATION.cff")
DATE_RELEASED_STR = "date-released"

VERSION_GLOBS = [
    "*/__init__.py",
    "CITATION.cff",
    "pyproject.toml",
]

VERSION_PATTERN = r"(^_*version_*\s*[:=]\s\").*\""

KAPALO_IMGS_DIR = Path("data/kapalo_imgs")
KAPALO_IMGS_ORIG_DIR = Path("data/kapalo_imgs_orig")


@task
def requirements(c):
    """
    Sync requirements.
    """
    c.run("nox --session requirements")


@task(pre=[requirements])
def format_and_lint(c):
    """
    Format and lint everything.
    """
    c.run("nox --session format_and_lint")


@task
def update_version(c):
    """
    Update pyproject.toml and package/__init__.py version strings.
    """
    c.run("nox --session update_version")


@task(pre=[requirements, update_version])
def ci_test(c, python=""):
    """
    Test suite for continous integration testing.

    Installs with pip, tests with pytest and checks coverage with coverage.
    """
    python_version = "" if len(python) == 0 else f"-p {python}"
    c.run(f"nox --session tests_pip {python_version}")


@task(pre=[requirements, update_version])
def docs(c):
    """
    Make documentation to docs using nox.
    """
    print("Making documentation.")
    c.run("nox --session docs")


@task(pre=[requirements])
def notebooks(c):
    """
    Execute and fill notebooks.
    """
    print("Executing and filling notebooks.")
    c.run("nox --session notebooks")


@task(pre=[requirements, update_version])
def build(c):
    """
    Build package with poetry.
    """
    print("Building package with poetry.")
    c.run("nox --session build")


@task(pre=[requirements])
def typecheck(c):
    """
    Typecheck ``kapalo_py`` with ``mypy``.
    """
    print("Typechecking Python code with mypy.")
    c.run("nox --session typecheck")


@task(pre=[requirements])
def performance_profile(c):
    """
    Profile kapalo_py performance with ``pyinstrument``.
    """
    print("Profiling kapalo_py performance with pyinstrument.")
    c.run("nox --session profile_performance")


@task
def citation(c):
    """
    Sync and validate CITATION.cff.
    """
    print("Updating CITATION.cff date")
    citation_text = CITATION_CFF_PATH.read_text()
    citation_lines = citation_text.splitlines()
    if DATE_RELEASED_STR not in citation_text:
        raise ValueError(
            f"Expected to find {DATE_RELEASED_STR} str in {CITATION_CFF_PATH}."
            f"\nCheck & validate {CITATION_CFF_PATH}."
        )
    date = strftime("%Y-%m-%d")
    new_lines = [
        line if "date-released" not in line else f'date-released: "{date}"'
        for line in citation_lines
    ]
    CITATION_CFF_PATH.write_text("\n".join(new_lines))

    print("Validating CITATION.cff")
    c.run("nox --session validate_citation_cff")


@task
def changelog(c, latest_version=""):
    """
    Generate changelog.
    """
    c.run(f"nox --session changelog -- {latest_version}")


@task(
    pre=[
        requirements,
        update_version,
        format_and_lint,
        ci_test,
        build,
        docs,
        citation,
        changelog,
    ]
)
def prepush(_):
    """
    Test suite for locally verifying continous integration results upstream.
    """


@task
def pre_commit(c, only_run=False, only_install=False):
    """
    Verify that pre-commit is installed, install its hooks and run them.
    """
    cmd = "pre-commit --help"
    try:
        c.run(cmd, hide=True)
    except Exception:
        print(f"Could not run '{cmd}'. Make sure pre-commit is installed.")
        raise

    if not only_run:
        c.run("pre-commit install")
        c.run("pre-commit install --hook-type commit-msg")
        print("Hooks installed!")

    if not only_install:
        print("Running on all files.")
        try:
            c.run("pre-commit run --all-files")
        except Exception:
            print("pre-commit run formatted files!")


@task(pre=[prepush], post=[pre_commit])
def tag(c, tag="", annotation=""):
    """
    Make new tag and update version strings accordingly
    """
    if len(tag) == 0:
        raise ValueError("Tag string must be specified with '--tag=*'.")
    if len(annotation) == 0:
        raise ValueError("Annotation string must be specified with '--annotation=*'.")

    # Create changelog with 'tag' as latest version
    c.run(f"nox --session changelog -- {tag}")

    # Remove v at the start of tag
    tag = tag if "v" not in tag else tag[1:]

    # Iterate over all files determined from VERSION_GLOBS
    for path in chain(*[Path(".").glob(glob) for glob in (VERSION_GLOBS)]):

        # Collect new lines
        new_lines = []
        for line in path.read_text().splitlines():

            # Substitute lines with new tag if they match pattern
            substituted = re.sub(VERSION_PATTERN, r"\g<1>" + tag + r'"', line)

            # Report to user
            if line != substituted:
                print(
                    f"Replacing version string:\n{line}\nin"
                    f" {path} with:\n{substituted}\n"
                )
                new_lines.append(substituted)
            else:
                # No match, append line anyway
                new_lines.append(line)

        # Write results to files
        path.write_text("\n".join(new_lines))

    cmds = (
        "# Run pre-commit to check files.",
        "pre-commit run --all-files",
        "git add .",
        "# Make sure only version updates are committed!",
        "git commit -m 'docs: update version'",
        "# Make sure tag is proper!",
        f"git tag -a v{tag} -m '{annotation}'",
    )
    print("Not running git cmds. See below for suggested commands:\n---\n")
    for cmd in cmds:
        print(cmd)


@task(
    pre=[
        prepush,
        notebooks,
        typecheck,
        performance_profile,
    ]
)
def make(_):
    """
    Make all.
    """
    print("---------------")
    print("make successful.")


@task
def image_convert(
    c, orig_img_dir=str(KAPALO_IMGS_ORIG_DIR), converted_img_dir=str(KAPALO_IMGS_DIR)
):
    """
    Convert kapalo images to smaller size.

    TODO: Change to python resizer.
    """
    orig_img_path = Path(orig_img_dir)
    converted_img_path = Path(converted_img_dir)
    # Convert images to smaller
    for image in orig_img_path.glob("*.jpg"):
        new_path = converted_img_path / image.name
        c.run(f"convert '{image}' -resize 1000x1000 '{new_path}'")


@task(post=[image_convert])
def kapalo_update(c):
    """
    Download and update kapalo test data.

    TODO: Allow specifying drive.
    """
    # kapalo.sqlite and backup paths
    kapalo_sql_path = Path("data/kapalo_sql/kapalo.sqlite")
    kapalo_sql_backup_path = Path("data/kapalo.sqlite.backup")

    # Make dirs
    kapalo_sql_dir = Path("data/kapalo_sql")
    for kapalo_dir in (kapalo_sql_dir, KAPALO_IMGS_DIR, KAPALO_IMGS_ORIG_DIR):
        kapalo_dir.mkdir(exist_ok=True, parents=True)

    # Remove old backup
    kapalo_sql_backup_path.unlink(missing_ok=True)

    if kapalo_sql_path.exists():
        # backup current
        copy(kapalo_sql_path, kapalo_sql_backup_path)

    # Download new kapalo.sqlite
    c.run("rclone sync nialovdrive:kapalo_sql data/kapalo_sql")

    # Download images
    c.run("rclone sync nialovdrive:kapalo_imgs data/kapalo_imgs_orig")


@task
def exports_to_shp(c):
    """
    Convert exports to shapefiles.

    TODO: Is fiona a strict dependency?
    TODO: Export to onedrive good idea?
    """
    # Export as geopackages and csvs
    c.run("python -m kapalo_py export-observations")

    # Make directories
    exports = Path("exports")
    exports_shp = exports / "as_shp"
    exports_shp.mkdir(parents=True, exist_ok=True)

    # Iterate over exported and find geopackages
    for path in exports.iterdir():
        if "gpkg" in path.suffix:
            new_name = path.with_suffix(".shp").name
            new_path = exports_shp / new_name
            new_path.unlink(missing_ok=True)
            c.run(
                " ".join(
                    [
                        "fio",
                        "dump",
                        str(path),
                        "|",
                        "fio",
                        "load",
                        str(new_path),
                        "--driver",
                        "Shapefile",
                        "--src_crs",
                        "EPSG:4326",
                        "--dst_crs",
                        "EPSG:3067",
                    ]
                )
            )

    # Sync shapefiles to onedrive
    c.run("rclone sync exports nialovdrive:kapalo_exports ")


@task
def push_map(c):
    """
    Upload compiled map to GitHub.

    TODO: Allow specifying website dir.
    """
    with c.cd("live-mapping"):
        c.run("git add .")
        c.run("git commit -m 'update webmap'")
        c.run("git push")


@task
def compile_and_push_jon_map(c):
    """
    Compile and push jon's map.
    """
    web_dir = Path("jon-aland-karikko-mapping")
    data_dir = Path("data_jon")
    map_index = web_dir / "index.html"
    map_imgs = web_dir / "kapalo_imgs"
    orig_img_path = data_dir / "kapalo_imgs_orig"
    img_path = data_dir / "kapalo_imgs"
    sqlite_path = data_dir / "kapalo_sql"
    project_str = "KARIKKO "

    c.run(
        "invoke image-convert --orig-img-dir "
        f"{orig_img_path} --converted-img-dir {img_path}"
    )

    c.run(
        " ".join(
            [
                "python",
                "-m",
                "kapalo_py",
                "compile-webmap",
                "--kapalo-sqlite-path",
                str(sqlite_path),
                "--kapalo-imgs-path",
                str(img_path),
                "--map-save-path",
                str(map_index),
                "--map-imgs-path",
                str(map_imgs),
                "--project",
                f"'{project_str}'",
                "--no-add-extra",
            ]
        )
    )

    with c.cd(web_dir):

        c.run("git add .")
        c.run("git commit -m 'update jon map'")
        c.run("git push")
