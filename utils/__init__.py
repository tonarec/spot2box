"""Utils functions for Spot2Box"""
import re
from pathlib import Path
import json


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


def compute_spotdl_filename(playlist_name, playlist_description, remove_tags=True) -> str:
    """Compute the SpotDL file according to the playlist metadata.

    Args:
        playlist_name (_type_): The Spotify playlist name
        playlist_description (_type_): The Spotify playlist description
        remove_tags (bool, optional): If tags markers `[]` should be removed
            from the playlist name. Defaults to True.
    """
    return ''


def is_valid_spotify_url(url: str) -> bool:
    """Check if the URL is a valid Spotify playlist URL.

    Args:
        url (str): The URL to check

    Returns:
        bool: If valid or not
    """
    if not ('open.spotify.com' in url and 'playlist' in url):
        return False
    return True


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
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return False
    if data.get('type') != 'sync' or data.get('query') is None or data.get('songs') is None:
        return False
    return True
