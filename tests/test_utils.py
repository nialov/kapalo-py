"""
Tests for utils.py.
"""

import numpy as np
import pytest
from hypothesis import given
from hypothesis.strategies import floats

import tests
from kapalo_py import utils


@pytest.mark.parametrize(
    "azimuth,declination_value,assume_result", tests.test_apply_declination_fix_params()
)
def test_apply_declination_fix_parametrize(azimuth, declination_value, assume_result):
    """
    Test apply_declination_fix with pytest parametrize.
    """
    _test_apply_declination_fix(
        azimuth=azimuth,
        declination_value=declination_value,
        assume_result=assume_result,
    )


@given(floats(), floats())
def test_apply_declination_fix_hypothesis(azimuth, declination_value):
    """
    Test apply_declination_fix with pytest parametrize.
    """
    _test_apply_declination_fix(
        azimuth=azimuth,
        declination_value=declination_value,
        assume_result=None,
    )


def _test_apply_declination_fix(azimuth, declination_value, assume_result):
    """
    Test apply_declination_fix.
    """
    invalid_input = not (
        (0.0 <= azimuth <= 360.0)
        and (-360.0 <= declination_value <= 360.0)
        and (not any(np.isnan((azimuth, declination_value))))
    )
    result = utils.apply_declination_fix(azimuth, declination_value)
    if invalid_input:
        assert result == azimuth or np.isnan(result)
        return
    assert 0.0 <= result <= 360.0

    if assume_result is not None:
        assert np.isclose(result, assume_result)
