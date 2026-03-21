"""
Module that handle Spot2Box configuration.
"""

import json
import os
from argparse import Namespace
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from platformdirs import PlatformDirs

APP_NAME = 'Spot2Box'
CONFIG_FILENAME = 'config'
LOG_FILENAME = 'Spot2Box.log'
SYNC_FOLDER_NAME = 'SyncFiles'


def get_appdata_path() -> Path:
    """Get the path to the spot2box data folder. If the folder does not exists, it will be created.

    Returns:
        Path: The path of the Spot2Box data folder
    """

    dirs = PlatformDirs(
        appname=APP_NAME,
        appauthor=False,
        roaming=False,
        ensure_exists=True
    )
    appdata_dir = dirs.user_data_dir
    return Path(appdata_dir)


def get_sync_folder_path() -> Path:
    """Get the sync folder path.

    Returns:
        Path: The path of the sync folder
    """

    sync_folder = get_appdata_path().joinpath(SYNC_FOLDER_NAME)
    os.makedirs(sync_folder, exist_ok=True)
    return sync_folder


def get_config_filepath() -> Path:
    """Get the config file path.

    Returns:
        Path: The path of the config file
    """

    return get_appdata_path().joinpath(CONFIG_FILENAME)


def get_log_filepath() -> Path:
    """Get the log file path.

    Returns:
        Path: The path of the log file
    """

    return get_appdata_path().joinpath(LOG_FILENAME)


def get_config() -> "Spot2BoxConfig":
    """Get the Spot2Box config. Create a default one if not found in the appdata directory.

    Returns:
        Spot2BoxConfig: A configuration instance of the existing configuration, or defaults.
    """

    config_file = get_config_filepath()
    if not config_file.exists():
        config = Spot2BoxConfig()
        config.output = PlatformDirs().user_music_dir
        return config

    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return Spot2BoxConfig(**data)


@dataclass
class Spot2BoxConfig():
    """
    Handle core configuration for Spot2Box.
    """

    # Spot2Box
    output: str = None
    urls: list[str] = field(default_factory=list)
    spotdl_files: list[str] = field(default_factory=list)
    save_sync_file: bool = True

    # Spotify
    spotify_client: str = None
    spotify_secret: str = None

    # Rekordbox
    rekordbox_xml: str = None
    rekordbox_path: str = None
    add_only: bool = False
    sort_playlist: bool = True
    delete_standalone_track: bool = False
    force_kill: bool = False
    open_rekordbox: bool = True

    @classmethod
    def from_namespace(cls, args: Namespace) -> "Spot2BoxConfig":
        """Create a Spot2BoxConfig instance from a Namespace. Only takes arguments that matches
        the configuration.

        If an argument as not been specified from the CLI, the current value from
        the configuration will be used.

        Args:
            args (Namespace): The Namespace object to create the instance from.

        Returns:
            Spot2BoxConfig: The Spot2BoxConfig instance.
        """

        settings = {}

        for f in fields(cls):
            key = f.name
            value = getattr(args, key, None)
            if value is not None:
                settings[key] = value

        return cls(**settings)

    def to_namespace(self) -> Namespace:
        """Create a Namespace object from the instance.

        Returns:
            Namespace: The Namespace object created from the instance.
        """

        args = Namespace(**asdict(self))
        return args

    def override(self, args: Namespace):
        """Override the configuration fields with a Namespace object.

        Args:
            args (Namespace): The Namespace object used to override the configuration fields.
        """

        for f in fields(self):
            key = f.name
            value = getattr(args, key, None)
            if value is not None:
                setattr(self, key, value)

    def save(self):
        """Save the configuration fields to the configuration file."""

        config_file = get_config_filepath()
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=4)
