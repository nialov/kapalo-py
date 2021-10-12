"""
kapalo_py.

Kapalo data extraction and processing
"""

__version__ = "0.0.0.post120.dev0+cb7e195"

import logging
import sys
from datetime import datetime

import structlog
from pythonjsonlogger import jsonlogger
from structlog.stdlib import get_logger

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
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


def setup_module_logging(
    logging_level_int: int = logging.WARNING,
    json_indent: int = LOGGING_JSON_INDENT,
):
    """
    Set up logging level.

    Default is WARNING.
    """
    # Set up structlog logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        wrapper_class=structlog.make_filtering_bound_logger(
            min_level=logging_level_int - 10,
        ),
        cache_logger_on_first_use=True,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    # Set up stdlib logging
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s", json_indent=json_indent
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging_level_int)

    logger = get_logger()
    logger.info(
        "Set up logging level for kapalo-py.",
        logging_level_int=logging_level_int,
    )


setup_module_logging()
