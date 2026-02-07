"""Main module of SpotBox"""

import argparse
import logging
import sys
from utils import logger
from wrappers.rekordbox import RekordboxWrapper

parser = argparse.ArgumentParser(
    prog='SpotBox - Spotify to Rekordbox playlist manager',
    description='Manage your Rekordbox playlists directly from Spotify')

parser.add_argument('-x', '--rekordbox-file', type=str,
                    dest='rekordbox_file', help='The rekordbox.xml to update')
parser.add_argument('-r', '--rekordbox-path', type=str,
                    dest='rekordbox_path', help='The Rekordbox installation path')
parser.add_argument('-s', '--spotdl-file', type=str, dest='spotdl_files', action='append',
                    help='SpotDL file to use as reference')
parser.add_argument('-client', '--spotify-client', type=str, dest='spotify_client',
                    help='The Spotify Client ID to use for the API')
parser.add_argument('-secret', '--spotify-secret', type=str, dest='spotify_secret',
                    help='The Spotify Secret to use for the API')

logger.init_logger(level=logging.DEBUG)


def main():
    """Main function of SpotBox"""
    args = parser.parse_args()

    # Check arguments for rekordbox
    path = args.rekordbox_path
    xml = args.rekordbox_file
    if xml is None and path is None:
        logging.error(
            'Set the Rekordbox installation path and/or a rekordbox.xml file')
        sys.exit(0)

    # Check arguments for spotdl
    for spotdl_file in args.spotdl_files:
        if not spotdl_file.endswith('.spotdl'):
            logging.error('File %s is not a valid SpotDL file', spotdl_file)
            sys.exit(0)

    wrapper = RekordboxWrapper(xml)
    wrapper.print_playlists()
    playlists = wrapper.get_playlists('HOUSE')
    for playlist in playlists:
        logging.info(playlist.Name)
    test_playlist = wrapper.get_or_create_playlist('TEST')
    test2_playlist = wrapper.get_or_create_playlist('TEST')
    print()


if __name__ == '__main__':
    main()
