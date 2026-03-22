"""Module that handle a wrapper for SpotDL"""

import logging
from pathlib import Path
from typing import Any, Dict

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

from spot2box import utils
from spot2box.core.config import Spot2BoxConfig, get_sync_folder_path
from spot2box.models.spotdl_file import SpotDLFile

SpotDLOrPath = SpotDLFile | str


class SpotDLWrapper:
    """
    Wrapper class wrapper for SpotDL.
    """

    config: Spot2BoxConfig

    def __init__(self, config: Spot2BoxConfig):
        self.config = config
        self._check_ffmpeg_install()
        self._init_spotdl_config()

    def _check_ffmpeg_install(self):
        """This method checks if ffmpeg is installed for spotdl, and download it if not."""

        if ffmpeg.is_ffmpeg_installed() is False:
            logging.info("FFmpeg is not installed. Downloading FFmpeg...")
            ffmpeg.download_ffmpeg()

    def _init_spotdl_config(self):
        """This method initialize the spotdl configuration and settings for both Spotify
        and the music downloader.

        A default configuration is created if no one found.
        Some settings are overrided for better compatibility with spot2box.
        """

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
        """Compute the correct filepath for the song depending on the settings.

        Args:
            song (Song): A song object to use as reference.

        Returns:
            Path: The computed filepath of the song.
        """

        filepath = formatter.create_file_name(
            song,
            self.config.output,
            self.downloader.settings["format"],
            self.downloader.settings["restrict"],
        )
        return filepath

    def process_spotdl_file(self, file: SpotDLOrPath) -> SpotDLFile:
        """Process a spotdl file in sync mode.

        Download track in sync mode from a spotdl file, then load the spotdl file and return
        the corresponding SpotDLFile instance.

        Args:
            filepath (str): The filepath of the spotdl file.

        Returns:
            SpotDLFile: An instance to handle data of the spotdl file.
        """

        if isinstance(file, str):
            spotdl_file = SpotDLFile.from_filepath(file)
        else:
            spotdl_file = file

        sync(query=[spotdl_file.path.as_posix()], downloader=self.downloader)
        spotdl_file.reload()
        return spotdl_file

    def process_spotify_url(self, url: str, filename: str = None) -> SpotDLFile:
        """Process a Spotify URL in sync mode.

        This method download songs from an URL, then loads the spotdl file and return
        the corresponding SpotDLFile instance.

        This method search for a corresponding spotdl file in the appdata directory.
        If a spotdl file is found, it will be updated with the new URL.

        If sync mode is enabled, a spotdl file is created in the appdata directory.

        Args:
            url (str): The Spotify playlist URL to process.
            filename (str, optional): A specific filename for the sync file. Defaults to None.

        Returns:
            SpotDLFile: An instance corresponding to the spotdl file.
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

    def get_playlist_metadata(self, url: str) -> Dict[str, Any]:
        """Get a dictionary with the metadata of the playlist.

        Args:
            url (str): A Spotify playlist URL.

        Returns:
            Dict[str, Any]: The metadata of the playlist.
        """

        metadata, _ = Playlist.get_metadata(url)
        return metadata

    def get_genre(self, song: Song, index=0) -> str:
        """Get the genre of a song.

        Args:
            song (Song): A song object.
            index (int, optional): Index of genre to get. Defaults to 0.

        Returns:
            str: _description_
        """

        if len(song.genres) > 0:
            return song.genres[index]
        return None

    def get_id3_separator(self) -> str:
        """Get the configured ID3 separator or default if not found in config.

        Returns:
            str: The ID3 separator.
        """

        default = DOWNLOADER_OPTIONS.get('id3_separator')
        return self.downloader.settings.get('id3_separator', default)
