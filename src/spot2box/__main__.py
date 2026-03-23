"""
Main module of SpotBox.
"""

import logging
import sys

from spot2box import Spot2Box, utils
from spot2box.core.config import get_config
from spot2box.utils import logger
from spot2box.utils.parser import parse_args

logger.init_logger(level=logging.DEBUG)


def main():
    """
    Entry point of Spot2Box CLI.
    """

    args = parse_args()
    config = get_config()
    config.override(args)

    # Check for valid spotdl files
    for spotdl_file in config.spotdl_files:
        if not utils.is_valid_spotdl_file(spotdl_file):
            logging.error('File "%s" is not a valid SpotDL file', spotdl_file)
            sys.exit(0)

    for url in config.urls:
        if not utils.is_valid_spotify_url(url):
            logging.error('Invalid Spotify playlist URL "%s"', url)
            sys.exit(0)

    spot2box = Spot2Box(config)

    for url in config.urls:
        spot2box.process_spotify_url(url)

    for spotdl_file in config.spotdl_files:
        spot2box.process_spotdl_file(spotdl_file)

    if args.save_config:
        config.save()


if __name__ == '__main__':
    main()
