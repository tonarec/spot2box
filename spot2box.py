"""Main module of SpotBox"""

import argparse
import logging
import sys
import os
import json

from utils import logger
from wrappers.rekordbox import RekordboxWrapper
from wrappers.spotdl import SpotDLWrapper
from utils.spotify import remove_intl_from_url

parser = argparse.ArgumentParser(
    prog='SpotBox - Spotify to Rekordbox playlist manager',
    description='Manage your Rekordbox playlists directly from Spotify')

parser.add_argument('-xml', '--rekordbox-xml', type=str,
                    dest='rekordbox_xml', help='The rekordbox.xml to update')
parser.add_argument('-r', '--rekordbox-path', type=str,
                    dest='rekordbox_path', help='The Rekordbox installation path')
parser.add_argument('-f', '--spotdl-file', type=str, dest='spotdl_files', action='append',
                    help='SpotDL file to use as reference')
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
        if not spotdl_file.endswith('.spotdl'):
            logging.error('File %s is not a valid SpotDL file', spotdl_file)
            sys.exit(0)

    rb_wrapper = RekordboxWrapper(xml)
    spot_wrapper = SpotDLWrapper(args)

    # rb_wrapper.print_playlists(expand=True)
    # rb_wrapper.print_artists()
    # rb_wrapper.print_albums()

    for spotdl_file in args.spotdl_files:
        # Load the spotdl file
        with open(spotdl_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        # Retrieve the song objects
        songs = spot_wrapper.get_songs(spotdl_file)

        for query in file_data.get('query'):
            url = remove_intl_from_url(query)

            if not ("open.spotify.com" in url and "playlist" in url):
                logging.warning(
                    'Ignoring non valid playlist query in spotdl file: %s', url)
                continue

            metadata = spot_wrapper.get_playlist_metadata(url)
            name = metadata.get('name')
            description = metadata.get('description')
            logging.info('Processing playlist %s', name)
            logging.info('    %s', description)

            # TODO: Compute safe playlist name
            rb_playlist_name = 'TestPlaylist_SpotDL'

            # Filtering songs for the current playlist
            playlist_songs = [song for song in songs if song.list_url == url]
            sorted_songs = spot_wrapper.sort_songs(playlist_songs)
            for current_song in sorted_songs:

                # Check for file downloaded and present in the rekordbox database
                filepath = spot_wrapper.compute_filepath(current_song)
                if not os.path.isfile(filepath):
                    logging.warning(
                        'Skipping track file not found: %s', filepath
                    )
                    # TODO: Download missing track if enabled
                    continue

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

                # Add the tracks to the playlist
                rb_wrapper.add_track_to_playlist(filepath, rb_playlist_name)

    rb_wrapper.apply_changes()


if __name__ == '__main__':
    main()
