"""
Global pytest fixtures.
"""
from pathlib import Path

import pytest

from kapalo_py import kapalo_map


@pytest.fixture
def fix_images(tmp_path: Path):
    """
    Make directory with .jpg extensioned empty files.
    """
    tempdir: Path = tmp_path / "tempdir"
    tempdir.mkdir(exist_ok=False, parents=True)
    for i in range(5):
        (tempdir / f"{i}.jpg").touch()

    yield tempdir

    for path in tempdir.iterdir():
        path.unlink()
    tempdir.rmdir()


@pytest.fixture
def fix_observations():
    """
    Make Observations.
    """
    path = Path("tests/sample_data/kapalo_sql")
    kapalo_tables = kapalo_map.read_kapalo_tables(path)
    observations = kapalo_map.gather_observation_data(
        kapalo_tables[0], exceptions=dict()
    )
    yield observations
