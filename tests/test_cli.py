"""
Tests for cli entrypoints.
"""
from traceback import print_tb

import pytest
from click.testing import Result
from typer.testing import CliRunner

import tests
from kapalo_py import cli

CLI_RUNNER = CliRunner()


def click_error_print(result: Result) -> None:
    """
    Print click result traceback.
    """
    if result.exit_code == 0:
        return
    assert result.exc_info is not None
    _, _, tb = result.exc_info
    # print(err_class, err)
    print_tb(tb)
    print(result.output)
    raise Exception(result.exception)


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
        cli._setup_logging(logging_level=logging_level)
    except Exception:
        if will_fail:
            return
        raise


@pytest.mark.parametrize(
    "entrypoint",
    ["compile-webmap", "export-observations", "resize-images", "remote-update"],
)
def test_entrypoints(entrypoint: str):
    """
    Test simply that entrypoints respond.
    """
    result = CLI_RUNNER.invoke(app=cli.APP, args=[entrypoint, "--help"])

    # Raises exception if invocation fails
    click_error_print(result)
