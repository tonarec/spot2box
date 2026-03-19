"""Main module of SpotBox"""

import argparse
import logging
import sys

from spot2box import Spot2Box, utils
from spot2box.core.config import get_config
from spot2box.utils import logger

parser = argparse.ArgumentParser(
    prog='SpotBox - Spotify to Rekordbox playlist manager',
    description='Manage your Rekordbox playlists directly from Spotify')

parser.add_argument('-x', '--rekordbox-xml', type=str,
                    dest='rekordbox_xml', help='The rekordbox.xml to update.')
parser.add_argument('-r', '--rekordbox-path', type=str,
                    dest='rekordbox_path', help='The Rekordbox installation path.')
parser.add_argument('-f', '--spotdl-file', type=str, dest='spotdl_files', action='append',
                    help='SpotDL files to use as inputs.')
parser.add_argument('-u', '--url', type=str, dest='urls', action='append',
                    help='Spotify Playlist URLs to process.')
parser.add_argument('--add-only', dest='add_only', action='store_true',
                    help='Only add new tracks in Rekordbox playlists.')
parser.add_argument('--spotify-client', type=str, dest='spotify_client',
                    help='The Spotify Client ID to use for the API.')
parser.add_argument('--spotify-secret', type=str, dest='spotify_secret',
                    help='The Spotify Secret to use for the API.')
parser.add_argument('-o', '--output', type=str, dest='output',
                    help='The folder of tracks.')
parser.add_argument('-s', '--save', dest='save_config', action='store_true',
                    help='Save configuration into appdata.')
parser.add_argument('--open', dest='open_rekordbox', action='store_true',
                    help='Open Rekordbox at the end.')


logger.init_logger(level=logging.DEBUG)


def main():
    """Main function of SpotBox"""
    args = parser.parse_args()
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
