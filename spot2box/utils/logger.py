"""Module that initialize the logger"""
import logging
import sys

from spot2box.core import config
from spot2box.utils import info


def init_logger(level: int = logging.INFO):
    """Initialize the logger.

    Args:
        level (int): The logging level
    """
    filepath = config.get_log_filepath()
    logging.basicConfig(level=level,
                        format='%(asctime)s | %(levelname)-7s | %(module)-9s |  %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[
                            logging.FileHandler(filepath),
                            logging.StreamHandler(sys.stdout)
                        ])

    app_name = config.APP_NAME
    version = info.get_version()
    author = info.get_author()
    logging.info('%s v%s (%s)', app_name, version, author)
