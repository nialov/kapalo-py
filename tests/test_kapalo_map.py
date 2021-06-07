"""
Tests for kapalo_map.py.
"""

from pathlib import Path

import pytest

import kapalo_py.kapalo_map as kapalo_map
import tests


@pytest.mark.parametrize("html_str", tests.test_add_local_stylesheet_params())
def test_add_local_stylesheet(html_str):
    """
    Test add_local_stylesheet.
    """
    style_path = Path("data/styles.css")
    assert "style" in html_str
    assert isinstance(html_str, str)
    result = kapalo_map.add_local_stylesheet(html_str, local_stylesheet=style_path)

    assert isinstance(result, str)
    assert style_path.name in result

    assert len(result) > len(html_str)
