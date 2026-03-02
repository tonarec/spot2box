"""Utils functions for Spot2Box"""
import json
import os
import re
import uuid
from json import JSONDecodeError
from pathlib import Path

from core import config

PLAYLIST_DESC_PATTERN = re.compile(r"playlist:\"*(.*)\"*")
GENRE_DESC_PATTERN = re.compile(r"genre:\"*(.*)\"*")


def remove_intl_from_url(url: str) -> str:
    """Removes the internatial parameter from URL.

    Args:
        url (str): The URL to clean

    Returns:
        str: The new URL
    """
    url = re.sub(r"\/intl-\w+\/", "/", url)
    return url


def remove_params_from_url(url: str) -> str:
    """Removes all parameters from URL.

    Args:
        url (str): The URL to clean

    Returns:
        str: The cleaned URL
    """
    splits = url.split('?')
    return splits[0]


def compute_spotdl_filename(url: str) -> str:
    """Compute the SpotDL file according to the playlist URL. If the URL is invalid,
    a random generated UUID is used for the base name. 

    Args:
        url (_type_): The Spotify playlist URL
    """

    if is_valid_spotify_url(url):
        # Extracting playlist ID
        parts = url.split('/playlist/')
        tail = parts[-1]
        base = tail.split('?')[0]
    else:
        # Generate random UUID and get node part
        base = uuid.uuid4().node

    return base + '.spotdl'


def is_valid_spotify_url(url: str) -> bool:
    """Check if the URL is a valid Spotify playlist URL.

    Args:
        url (str): The URL to check

    Returns:
        bool: If valid or not
    """
    if ('open.spotify.com' in url and 'playlist' in url):
        return True
    return False


def is_valid_spotdl_file(filepath: str) -> bool:
    """Check if the path exists and is a valid .spotdl file.

    Args:
        filepath (str): The file path

    Returns:
        bool: If valid or not
    """
    path = Path(filepath)
    if not path.exists() or path.suffix.lower() != '.spotdl':
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except JSONDecodeError:
        return False

    if not isinstance(data, dict):
        return False
    if data.get('type') != 'sync' or data.get('query') is None or data.get('songs') is None:
        return False

    return True


def search_first_spotdl_file(url: str, ignore_params: bool = True) -> str:
    """Search for the first SpotDL file that match the URL in the sync folder.

    Args:
        url (str): The URL used for the search
        ignore_params (bool, optional): If params in URL should be ignored. Defaults to True.

    Returns:
        str: The filepath of the .spotdl or `None`
    """

    sync_path = config.get_sync_folder_path()
    spotdl_files = search_spotdl_files(folder_path=sync_path)
    for spotdl_file in spotdl_files:
        if is_actual_sync_file(url, spotdl_file, ignore_params):
            return spotdl_file
    return None


def search_spotdl_files(folder_path: str) -> list[str]:
    """Search for all .spotdl files in the folder.

    Args:
        folder_path (str): The path of folder 

    Returns:
        list[str]: A list .spotdl filepath if found
    """

    result = []
    for dir_entry in os.scandir(folder_path):
        if dir_entry.is_file() and dir_entry.name.endswith('.spotdl'):
            result.append(dir_entry.path)
    return result


def is_actual_sync_file(url: str, spotdl_file: str, ignore_params: bool = True) -> bool:
    """Check if the SpotDL file is the one corresponding to the URL.

    Args:
        url (str): The URL to use as reference
        spotdl_file (str): The SpotDL file to check
        ignore_params (bool, optional): If parameters in URL should be ignored. Defaults to True.

    Returns:
        bool: If the SpotDL file is the correct one or `None`
    """

    if is_valid_spotdl_file(spotdl_file):
        with open(spotdl_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        query = data.get('query')
        for q in query:
            if url in q:
                return True
            if ignore_params:
                if q.split('?')[0] in url.split('?')[0]:
                    return True

    return False
