"""Main module of SpotBox"""

import argparse
import logging
import os
import sys
from pathlib import Path

import utils
from models.spotdl_file import SpotDLFile
from utils import logger
from wrappers.rekordbox import RekordboxWrapper
from wrappers.spotdl import SpotDLWrapper

parser = argparse.ArgumentParser(
    prog='SpotBox - Spotify to Rekordbox playlist manager',
    description='Manage your Rekordbox playlists directly from Spotify')

parser.add_argument('-xml', '--rekordbox-xml', type=str,
                    dest='rekordbox_xml', help='The rekordbox.xml to update')
parser.add_argument('-r', '--rekordbox-path', type=str,
                    dest='rekordbox_path', help='The Rekordbox installation path')
parser.add_argument('-f', '--spotdl-file', type=str, dest='spotdl_files', action='append',
                    help='SpotDL files to use as inputs')
parser.add_argument('-u', '--url', type=str, dest='urls', action='append',
                    help='Spotify playlist URLs to process')
parser.add_argument('-client', '--spotify-client', type=str, dest='spotify_client',
                    help='The Spotify Client ID to use for the API')
parser.add_argument('-secret', '--spotify-secret', type=str, dest='spotify_secret',
                    help='The Spotify Secret to use for the API')
parser.add_argument('-output', '--output', type=str, dest='output',
                    help='The folder of tracks')

logger.init_logger(level=logging.DEBUG)


def main():
    """Main function of SpotBox"""
    args = parser.parse_args()

    # Check arguments for rekordbox
    path = args.rekordbox_path
    xml = args.rekordbox_xml
    # if xml is None and path is None:
    #     logging.error(
    #         'Set the Rekordbox installation path and/or a rekordbox.xml file'
    #     )
    #     sys.exit(0)

    # Check for valid spotdl files
    for spotdl_file in args.spotdl_files:
        if not utils.is_valid_spotdl_file(spotdl_file):
            logging.error('File "%s" is not a valid SpotDL file', spotdl_file)
            sys.exit(0)

    for url in args.urls:
        if not utils.is_valid_spotdl_file(url):
            logging.error('Invalid Spotify playlist URL "%s"', url)
            sys.exit(0)

    rb_wrapper = RekordboxWrapper(xml)
    spot_wrapper = SpotDLWrapper(args)

    for spotdl_file in args.spotdl_files:
        # Load the spotdl file
        spotdl = SpotDLFile.from_filepath(spotdl_file)

        # Retrieve the song objects
        songs = spotdl.songs

        for query in spotdl.query:
            url = utils.remove_intl_from_url(query)
            if not utils.is_valid_spotify_url(url):
                logging.warning(
                    'Ignoring non valid Spotify playlist query in spotdl file: %s', url)
                continue

            metadata = spot_wrapper.get_playlist_metadata(url)
            name = metadata.get('name')
            description = metadata.get('description')
            logging.info('Processing playlist %s', name)
            logging.info('    %s', description)

            # TODO: Compute safe playlist name
            path = Path(spotdl_file)
            spotdl_filename = path.stem
            rb_playlist_name = spotdl_filename

            # Filtering songs for the current playlist
            playlist_songs = [song for song in songs if song.list_url == url]
            sorted_songs = spot_wrapper.sort_songs(playlist_songs)

            # Add missing songs to database
            track_paths = []
            for current_song in sorted_songs:

                # Check for file downloaded and present in the rekordbox database
                filepath = spot_wrapper.compute_filepath(current_song)
                if not os.path.isfile(filepath):
                    logging.warning(
                        'Skipping track file not found: %s', filepath
                    )
                    # TODO: Download missing track if enabled
                    continue

                track_paths.append(filepath)

                content = rb_wrapper.get_track_in_database(filepath)
                if content is None:
                    sep = spot_wrapper.get_id3_separator()
                    rb_wrapper.add_track_to_database(
                        path=filepath,
                        title=current_song.name,
                        artist=sep.join(current_song.artists),
                        album=current_song.album_name,
                        genre=current_song.genres[0] if current_song.genres else None
                    )

            # Sync tracks to the playlist
            rb_wrapper.sync_playlist(rb_playlist_name, track_paths)

    rb_wrapper.apply_changes()


if __name__ == '__main__':
    main()
