"""
Filter rules for columns.
"""

import logging


def in_range(number, min_value, max_value) -> bool:
    """
    Is number in range.
    """
    try:
        is_in_range = min_value <= number <= max_value
        return is_in_range
    except TypeError:
        logging.warning(
            "TypeError for number in in_range.",
            exc_info=True,
            extra=dict(number=number, min_value=min_value, max_value=max_value),
        )
    return False


def filter_dip(dip):
    """
    Filter dip.
    """
    return in_range(dip, 0.0, 90.0)


def filter_dip_dir(dip_dir):
    """
    Filter dip direction.
    """
    return in_range(dip_dir, 0.0, 360.0)
