"""Module that handle a wrapper for SpotDL"""

import json
import logging
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict
from copy import deepcopy

import utils
from spotdl.console.sync import sync
from spotdl.console.save import save
from spotdl.console.entry_point import generate_initial_config
from spotdl.download.downloader import Downloader
from spotdl.types.options import DownloaderOptions, SpotifyOptions
from spotdl.types.playlist import Playlist
from spotdl.types.song import Song
from spotdl.utils import ffmpeg, formatter
from spotdl.utils.config import (DOWNLOADER_OPTIONS, SPOTIFY_OPTIONS,
                                 create_settings_type, get_config)
from spotdl.utils.spotify import SpotifyClient

from models.spotdl_file import SpotDLFile


class SpotDLWrapper:

    def __init__(self, args: Namespace):
        self.__check_ffmpeg_install()
        self.__init_config(args)

    def __check_ffmpeg_install(self):
        if ffmpeg.is_ffmpeg_installed() is False:
            logging.info("FFmpeg is not installed. Downloading FFmpeg...")
            ffmpeg.download_ffmpeg()

    def __init_config(self, args: Namespace) -> bool:
        generate_initial_config()
        self.config = get_config()

        # Ensure correct parameters for spot2box
        self.config['load_config'] = True
        self.config['sync_without_deleting'] = True

        # Creating correct settings types
        spotify_config = create_settings_type(
            args, self.config, SPOTIFY_OPTIONS
        )
        downloader_settings = create_settings_type(
            args, self.config, DOWNLOADER_OPTIONS
        )

        spotify_options = SpotifyOptions(**spotify_config)
        downloader_options = DownloaderOptions(**downloader_settings)

        self.spotify_client = SpotifyClient.init(**spotify_options)
        self.downloader = Downloader(downloader_options)

    ############
    # File
    ############
    def compute_filepath(self, track: Song) -> Path:
        """Compute the correct filpath for the song according to the settings.

        Args:
            track (Song): A song object to use as reference

        Returns:
            Path: The corresponding path of the song
        """
        filepath = formatter.create_file_name(
            track,
            self.downloader.settings["output"],  # TODO: add output folder
            self.downloader.settings["format"],
            self.downloader.settings["restrict"],
        )
        return filepath

    def process_spotdl_file(self, filepath: str) -> SpotDLFile:
        # From a spotdl file process the normal sync mode
        # Then load the spotdl file and return the corresponding
        spotdl_file = SpotDLFile.from_filepath(filepath)
        sync(spotdl_file.path, self.downloader)
        spotdl_file.reload()
        return spotdl_file

    def process_spotify_url(self, url: str, filename: str = None) -> SpotDLFile:
        # From a Spotify URL process the sync mode with save path enabled
        # Then load the spotdl file and return the corresponding object
        metadata = self.get_playlist_metadata(url)
        if not filename:
            name = metadata['name']
            description = metadata['description']
            filename = utils.compute_spotdl_filename(
                playlist_name=name,
                playlist_description=description
            )
            filename += '.spotdl'

        # TODO: Compute fullpath for appdata
        filepath = filename

        # Copy needed to not overwrite settings
        downloader = deepcopy(self.downloader)
        downloader.settings["save_file"] = filename
        save(query=url, downloader=downloader)
        spotdl_file = SpotDLFile.from_filepath(filepath)
        return spotdl_file

    ############
    # Songs
    ############
    def get_songs(self, filepath: str) -> list[Song]:
        with open(filepath, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        songs = []
        for song_data in file_data['songs']:
            song = Song.from_dict(song_data)
            songs.append(song)
        return songs

    def sort_songs(self, tracks: list[Song]) -> list[Song]:
        sorted_tracks = list.copy(tracks)
        sorted_tracks.sort(key=lambda x: x.list_position or 0)
        return sorted_tracks

    def compare_files(self):
        # Make a copy of the current spotdl file
        # Perform actions with sync
        # Compare the new file and checks for addition/deletion of tracks
        # Return the list of added and deleted tracks (path)
        pass

    ############
    # Metadata
    ############
    def get_playlist_metadata(self, url: str) -> Dict[str, Any]:
        metadata, _ = Playlist.get_metadata(url)
        return metadata

    def get_genre(self, track: Song, pos=0) -> str:
        if len(track.genres) > 0:
            return track.genres[pos]
        return ''

    ############
    # Utils
    ############
    def get_id3_separator(self) -> str:
        """Get the configured ID3 separator or default if not found in config

        Returns:
            str: The separator
        """
        default = DOWNLOADER_OPTIONS.get('id3_separator')
        return self.downloader.settings.get('id3_separator', default)

    def print_songs(self):
        playlists = self.db.get_playlist()
        for playlist in playlists:
            logging.debug('Playlist: %s', playlist.Name)
            songs = playlist.Songs
            for song in songs:
                content = song.Content
                logging.debug('\t%s - %s', content.ArtistName, content.Title)
