"""
This module contains the entry point for the Spot2Box application.
It initializes the application configuration and wrappers.
"""

import logging

from spot2box import utils
from spot2box.core.config import Spot2BoxConfig, get_config
from spot2box.models.spotdl_file import SpotDLFile
from spot2box.wrappers.rekordbox import RekordboxWrapper
from spot2box.wrappers.spotdl import SpotDLWrapper


class Spot2Box():
    """
    Spot2Box class that simplify the process of syncing Spotify songs into Rekordbox.
    """

    def __init__(self, configuration: Spot2BoxConfig = None):
        self.config = configuration or get_config()
        self.rb_wrapper = RekordboxWrapper(self.config)
        self.spot_wrapper = SpotDLWrapper(self.config)

    def process_spotify_url(self, url: str):
        """Sync a Spotify playlist from an URL into Rekordbox.

        This method takes a Spotify playlist URL and download the songs in the playlist,
        then synchronize them to the corresponding Rekordbox playlist. If the Rekordbox playlist
        does not exist, it will be created.

        If a synchronize file already exist on the system, it will be used and updated.
        Otherwise a new sync file will be created.

        Args:
            url (str): A Spotify playlist URL.

        Raises:
            NotImplementedError: If save sync file is not enabled.
        """

        url = utils.remove_intl_from_url(url)
        spotdl_file = self.spot_wrapper.process_spotify_url(url)

        if spotdl_file is None:
            # TODO: Process downloaded tracks but not synced
            raise NotImplementedError(
                'Downloaded tracks without sync file is not implemented yet.'
            )

        self._sync_playlist(spotdl_file)

    def process_spotdl_file(self, filepath: str):
        """Sync a SpotDL file into Rekordbox.

        This method takes a SptoDL file and download the songs in the playlist,
        then synchronize them to the corresponding Rekordbox playlist. If the Rekordbox playlist
        does not exist, it will be created.

        Args:
            filepath (str): The file path to the spotdl file.
        """

        spotdl_file = self.spot_wrapper.process_spotdl_file(file=filepath)

        self._sync_playlist(spotdl_file)

    def _sync_playlist(self, spotdl_file: SpotDLFile):
        """Synchronize the spotdl file into the corresponding Rekordbox playlist.

        This method takes a spotdl sync file as argument, and use it as a reference of
        downloaded songs. For new downloaded songs not present in the Rekordbox database,
        a new content is added into the database.

        The Rekordbox playlist name is computed from the Spotify playlist metadata.
        Only tracks found on the system are synced into Rekordbox.

        Args:
            spotdl_file (SpotDLFile): The SpotDL sync file to use as reference.
        """

        playlist_url = spotdl_file.query[0]
        metadata = self.spot_wrapper.get_playlist_metadata(url=playlist_url)
        playlist_name = metadata.get('name')
        playlist_description = metadata.get('description')
        logging.info('Processing playlist %s', playlist_name)
        logging.info('    %s', playlist_description)

        rb_playlist_name = utils.compute_safe_playlist_name(metadata)

        # Filtering songs for the current playlist
        songs = utils.get_songs_by_playlist_url(playlist_url, spotdl_file)

        # Add missing songs to database
        tracks = []
        for song in songs:
            # Check for file downloaded and present in the system
            filepath = self.spot_wrapper.compute_filepath(song)
            if not filepath.exists():
                logging.warning('Skipping track file not found: %s', filepath)
                continue

            tracks.append(filepath)

            # Check if track is present in the database
            content = self.rb_wrapper.get_track_in_database(filepath)
            if content is None:
                sep = self.spot_wrapper.get_id3_separator()
                self.rb_wrapper.add_track_to_database(
                    path=filepath,
                    title=song.name,
                    artist=sep.join(song.artists),
                    album=song.album_name,
                    genre=song.genres[0] if song.genres else None
                )

        # Sync tracks to the playlist
        self.rb_wrapper.sync_playlist(rb_playlist_name, tracks)
