"""Module that handle a wrapper for SpotDL"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

from spotdl.console.download import download
from spotdl.console.entry_point import generate_initial_config
from spotdl.console.sync import sync
from spotdl.download.downloader import Downloader
from spotdl.types.options import DownloaderOptions, SpotifyOptions
from spotdl.types.playlist import Playlist
from spotdl.types.song import Song
from spotdl.utils import ffmpeg, formatter
from spotdl.utils.config import (DOWNLOADER_OPTIONS, SPOTIFY_OPTIONS,
                                 create_settings_type, get_config)
from spotdl.utils.spotify import SpotifyClient

import utils
from core.config import Spot2BoxConfig, get_sync_folder_path
from models.spotdl_file import SpotDLFile

SpotDLOrPath = Union[SpotDLFile, str]


class SpotDLWrapper:

    config: Spot2BoxConfig

    def __init__(self, config: Spot2BoxConfig):
        self.config = config
        self.__check_ffmpeg_install()
        self.__init_spotdl_config()

    def __check_ffmpeg_install(self):
        if ffmpeg.is_ffmpeg_installed() is False:
            logging.info("FFmpeg is not installed. Downloading FFmpeg...")
            ffmpeg.download_ffmpeg()

    def __init_spotdl_config(self) -> bool:
        generate_initial_config()
        spotdl_config = get_config()

        # Ensure correct parameters for spot2box
        spotdl_config['load_config'] = True
        spotdl_config['sync_without_deleting'] = True  # Avoid deleting tracks
        spotdl_config["lyrics_providers"] = []  # Avoid searching for lyrics
        args = self.config.to_namespace()

        # Creating correct settings types
        spotify_config = create_settings_type(
            args, spotdl_config, SPOTIFY_OPTIONS
        )
        downloader_settings = create_settings_type(
            args, spotdl_config, DOWNLOADER_OPTIONS
        )

        spotify_options = SpotifyOptions(**spotify_config)
        downloader_options = DownloaderOptions(**downloader_settings)

        self.spotify_client = SpotifyClient.init(**spotify_options)
        self.downloader = Downloader(downloader_options)

    def compute_filepath(self, song: Song) -> Path:
        """Compute the correct filpath for the song according to the settings.

        Args:
            song (Song): A song object to use as reference

        Returns:
            Path: The corresponding path of the song
        """

        filepath = formatter.create_file_name(
            song,
            self.config.output,
            self.downloader.settings["format"],
            self.downloader.settings["restrict"],
        )
        return filepath

    def process_spotdl_file(self, file: SpotDLOrPath) -> SpotDLFile:
        """Process a spotdl file in sync mode. Then load the spotdl file and return
        the corresponding SpotDLFile object.

        Args:
            filepath (str): The filepath of the spotdl file

        Returns:
            SpotDLFile: An instance corresponding to the spotdl file
        """

        if isinstance(file, str):
            spotdl_file = SpotDLFile.from_filepath(file)
        else:
            spotdl_file = file

        sync(query=spotdl_file.query, downloader=self.downloader)
        spotdl_file.reload()
        return spotdl_file

    def process_spotify_url(self, url: str, filename: str = None) -> SpotDLFile:
        """Process a Spotify URL in sync mode if enabled, or download mode. Then load 
        the spotdl file and return the corresponding SpotDLFile object.

        This method search for a corresponding spotdl file in the appdata directory.
        If a spotdl file is found, it will be updated with the new URL.

        If sync mode is enabled, a spotdl file is created in the appdata directory.

        Args:
            url (str): The Spotify playlist URL to process
            filename (str, optional): A specific filename for the sync file. Defaults to None.

        Returns:
            SpotDLFile: An instance corresponding to the spotdl file
        """

        # Check for corresponding spotdl file
        spotdl_file = utils.search_first_spotdl_file(url)
        if spotdl_file:
            spotdl_file.update_query(url)
            return self.process_spotdl_file(file=spotdl_file)

        # Process URL directly
        if not self.config.save_sync_file:
            download(query=[url], downloader=self.downloader)
            return None

        # Otherwise process a new URL
        if not filename:
            filename = utils.compute_spotdl_filename(url)

        filepath = get_sync_folder_path().joinpath(filename)

        # Update downloader settings and sync
        self.downloader.settings["save_file"] = filepath
        sync(query=[url], downloader=self.downloader)

        spotdl_file = SpotDLFile.from_filepath(filepath)
        return spotdl_file

    def sort_songs(self, songs: list[Song]) -> list[Song]:
        sorted_songs = list.copy(songs)
        sorted_songs.sort(key=lambda x: x.list_position or 0)
        return sorted_songs

    def compare_files(self):
        # Make a copy of the current spotdl file
        # Perform actions with sync
        # Compare the new file and checks for addition/deletion of tracks
        # Return the list of added and deleted tracks (path)
        pass

    def get_playlist_metadata(self, url: str) -> Dict[str, Any]:
        """Get a dictionary with the metadata of the playlist.

        Args:
            url (str): A Spotify playlist URL

        Returns:
            Dict[str, Any]: The metadata
        """
        metadata, _ = Playlist.get_metadata(url)
        return metadata

    def get_genre(self, song: Song, pos=0) -> str:
        if len(song.genres) > 0:
            return song.genres[pos]
        return ''

    def get_id3_separator(self) -> str:
        """Get the configured ID3 separator or default if not found in config.

        Returns:
            str: The separator
        """

        default = DOWNLOADER_OPTIONS.get('id3_separator')
        return self.downloader.settings.get('id3_separator', default)
