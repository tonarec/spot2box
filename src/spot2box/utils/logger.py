"""Module that initialize the logger"""
import logging
import sys
import tomllib as toml

from spot2box.core import config


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

    with open("pyproject.toml", "rb") as f:
        data = toml.load(f)

    project_info = data['project']
    app_name = project_info['name']
    version = project_info['version']
    author = project_info['authors'][0]['name']
    logging.info('%s v%s (%s)', app_name, version, author)
