"""
Tests for cli entrypoints.
"""
import pytest

import tests
from kapalo_py import cli


@pytest.mark.parametrize("origin_dir,extension", tests.test__resize_images_params())
@pytest.mark.parametrize("fixed_width", [400, 800])
@pytest.mark.parametrize("overwrite", [True, False])
def test__resize_images(origin_dir, extension, fixed_width, tmp_path, overwrite):
    """
    Test _resize_images.
    """
    assert origin_dir.exists()
    assert isinstance(overwrite, bool)
    origin_dir_files = list(origin_dir.glob(f"*.{extension}"))
    origin_dir_filecount = len(origin_dir_files)
    assert origin_dir_filecount > 0
    destination_dir = tmp_path / "destination_dir"
    cli._resize_images(
        origin_dir=origin_dir,
        destination_dir=destination_dir,
        extension=extension,
        fixed_width=fixed_width,
        overwrite=overwrite,
    )

    destination_dir_files = list(destination_dir.glob(f"*.{extension}"))
    destination_dir_filecount = len(destination_dir_files)

    assert origin_dir_filecount == destination_dir_filecount

    origin_dir_filesize = sum(path.stat().st_size for path in origin_dir_files)
    destination_dir_filesize = sum(
        path.stat().st_size for path in destination_dir_files
    )

    assert origin_dir_filesize > destination_dir_filesize


@pytest.mark.parametrize("logging_level,will_fail", tests.test__setup_logging_params())
def test__setup_logging(logging_level, will_fail):
    """
    Test _setup_logging.
    """
    try:
        result = cli._setup_logging(logging_level=logging_level)
    except Exception:
        if will_fail:
            return
        raise
    assert result is None
