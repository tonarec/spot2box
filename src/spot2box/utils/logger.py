"""
Module that initialize the logger.
"""

import logging
import sys
import tomllib as toml

from spot2box.core import config


def init_logger(level: int = logging.INFO):
    """Initialize the logger.

    Args:
        level (int): The logging level.
    """

    # [spotdl/utils/logging.py:172]
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("spotipy").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("syncedlyrics").setLevel(logging.WARNING)
    logging.getLogger("bandcamp_api").setLevel(logging.WARNING)
    logging.getLogger("beautifulsoup4").setLevel(logging.WARNING)
    logging.getLogger("pytube").setLevel(logging.ERROR)

    logging.getLogger("spotdl.download.progress_handler").setLevel(logging.WARNING)
    logging.getLogger("spotdl.download.downloader").setLevel(logging.WARNING)

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
