"""
Invoke tasks.

Most tasks employ nox to create a virtual session for testing.
"""
from pathlib import Path
from shutil import copy
from invoke import task
from invoke import UnexpectedExit

NOX_PARALLEL_SESSIONS = ("tests_pip",)

PACKAGE_NAME = "kapalo_py"
kapalo_imgs_dir = Path("data/kapalo_imgs")
kapalo_imgs_orig_dir = Path("data/kapalo_imgs_orig")


@task
def requirements(c):
    """
    Sync requirements.
    """
    c.run("nox --session requirements")


@task(pre=[requirements])
def lint(c):
    """
    Lint everything.
    """
    c.run("nox --session lint")


@task(pre=[requirements])
def nox_parallel(c):
    """
    Run selected nox test suite sessions in parallel.
    """
    # Run asynchronously and collect promises
    print(f"Running {len(NOX_PARALLEL_SESSIONS)} nox test sessions.")
    promises = [
        c.run(
            f"nox --session {nox_test} --no-color",
            asynchronous=True,
            timeout=360,
        )
        for nox_test in NOX_PARALLEL_SESSIONS
    ]

    # Join all promises
    results = [promise.join() for promise in promises]

    # Check if Result has non-zero exit code (should've already thrown error.)
    for result in results:
        if result.exited != 0:
            raise UnexpectedExit(result)

    # Report to user of success.
    print(f"{len(results)} nox sessions ran succesfully.")


@task
def update_version(c):
    """
    Update pyproject.toml version string.
    """
    c.run("nox --session update_version")


@task(pre=[requirements, update_version])
def ci_test(c):
    """
    Test suite for continous integration testing.

    Installs with pip, tests with pytest and checks coverage with coverage.
    """
    c.run("nox --session tests_pip")


@task(pre=[requirements, nox_parallel])
def test(_):
    """
    Run tests.

    This is an extensive suite. It first tests in current environment and then
    creates virtual sessions with nox to test installation -> tests.
    """


@task(pre=[requirements, update_version])
def docs(c):
    """
    Make documentation to docs using nox.
    """
    c.run("nox --session docs")


@task(pre=[requirements])
def notebooks(c):
    """
    Execute and fill notebooks.
    """
    c.run("nox --session notebooks")


@task(pre=[update_version, test, lint, docs, notebooks])
def make(_):
    """
    Make all.
    """
    print("---------------")
    print("make successful.")


@task
def image_convert(c):
    """
    Convert kapalo images to smaller size.
    """
    # Convert images to smaller
    for image in kapalo_imgs_orig_dir.glob("*.jpg"):
        new_path = kapalo_imgs_dir / image.name
        c.run(f"convert '{image}' -resize 1000x1000 '{new_path}'")


@task(post=[image_convert])
def kapalo_update(c):
    """
    Download and update kapalo test data.
    """
    # kapalo.sqlite and backup paths
    kapalo_sql_path = Path("data/kapalo_sql/kapalo.sqlite")
    kapalo_sql_backup_path = Path("data/kapalo.sqlite.backup")

    # Make dirs
    kapalo_sql_dir = Path("data/kapalo_sql")
    for kapalo_dir in (kapalo_sql_dir, kapalo_imgs_dir, kapalo_imgs_orig_dir):
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
                    ]
                )
            )
            # c.run(
            #     " ".join(
            #         [
            #             "geotrans",
            #             str(path),
            #             "--to_type",
            #             "shp",
            #             "--output",
            #             str(new_path),
            #         ]
            #     )

    # Sync shapefiles to onedrive
    c.run("rclone sync exports nialovdrive:kapalo_exports ")
