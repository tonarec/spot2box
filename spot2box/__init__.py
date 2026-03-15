import logging

from spot2box import utils
from spot2box.core.config import Spot2BoxConfig, get_config
from spot2box.models.spotdl_file import SpotDLFile
from spot2box.wrappers.rekordbox import RekordboxWrapper
from spot2box.wrappers.spotdl import SpotDLWrapper


class Spot2Box():
    def __init__(self, configuration: Spot2BoxConfig = None):
        self.config = configuration or get_config()
        self.rb_wrapper = RekordboxWrapper(self.config)
        self.spot_wrapper = SpotDLWrapper(self.config)

    def process_spotify_url(self, url: str):
        url = utils.remove_intl_from_url(url)
        spotdl_file = self.spot_wrapper.process_spotify_url(url)

        if spotdl_file is None:
            # TODO: Process downloaded tracks but not synced
            raise NotImplementedError(
                'Downloaded tracks without sync file is not implemented yet.'
            )

        self._sync_playlist(spotdl_file)

    def process_spotdl_file(self, filepath: str):
        # Perform spotdl sync processing
        spotdl_file = self.spot_wrapper.process_spotdl_file(file=filepath)

        self._sync_playlist(spotdl_file)

    def _sync_playlist(self, spotdl_file: SpotDLFile):
        # Once we have the SpotDLFile instance, get the target playlist name and object
        playlist_url = spotdl_file.query[0]
        metadata = self.spot_wrapper.get_playlist_metadata(url=playlist_url)
        playlist_name = metadata.get('name')
        playlist_description = metadata.get('description')
        logging.info('Processing playlist %s', playlist_name)
        logging.info('    %s', playlist_description)

        rb_playlist_name = utils.compute_safe_playlist_name(metadata)

        # Filtering songs for the current playlist
        songs = utils.get_playlist_songs(playlist_url, spotdl_file)

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
        self.rb_wrapper.apply_changes()
