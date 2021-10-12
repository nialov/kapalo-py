"""
Logging setup for kapalo-py.
"""

import logging
import sys
from datetime import datetime

from pythonjsonlogger import jsonlogger

LOGGING_JSON_INDENT = 2


class CustomJsonFormatter(jsonlogger.JsonFormatter):

    """
    Custom Json Formatter.

    https://github.com/madzak/python-json-logger
    """

    def add_fields(self, log_record, record, message_dict):
        """
        Add fields.
        """
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if log_record.get("timestamp") is None:
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level") is not None:
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname
        if log_record.get("linenumber") is None:
            log_record["linenumber"] = record.lineno
        if log_record.get("pathname") is None:
            log_record["pathname"] = record.pathname


def setup_module_logging(
    logging_level_int: int = logging.WARNING,
    json_indent: int = LOGGING_JSON_INDENT,
):
    """
    Set up logging level and format as JSON.

    Default level is WARNING. Logs are output to stderr.
    """
    # Set up stdlib logging to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    formatter = CustomJsonFormatter(json_indent=json_indent)
    stderr_handler.setFormatter(formatter)
    stderr_handler.setLevel(logging_level_int)
    root_logger = logging.getLogger()
    root_logger.addHandler(stderr_handler)
    logging.info(
        "Set up logging level.", extra=dict(logging_level_int=logging_level_int)
    )
