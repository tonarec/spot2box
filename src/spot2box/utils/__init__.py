"""
Utils methods for Spot2Box.
"""

import json
import os
import re
import unicodedata
import uuid
from html import unescape
from json import JSONDecodeError
from pathlib import Path

from spotdl.types.song import Song

from spot2box.core import config
from spot2box.models.spotdl_file import SpotDLFile

PLAYLIST_DESC_PATTERN = re.compile(r'playlist:\"(.*)\"')
GENRE_DESC_PATTERN = re.compile(r'genre:\"(.*)\*')


def remove_intl_from_url(url: str) -> str:
    """Removes the internatial parameter from URL.

    Args:
        url (str): The URL to clean.

    Returns:
        str: The new URL.
    """

    url = re.sub(r"\/intl-\w+\/", "/", url)
    return url


def remove_params_from_url(url: str) -> str:
    """Removes all parameters from URL.

    Args:
        url (str): The URL to clean.

    Returns:
        str: The cleaned URL.
    """

    splits = url.split('?')
    return splits[0]


def compute_spotdl_filename(url: str) -> str:
    """Compute the SpotDL filename according to the playlist URL. If the URL is invalid,
    a random generated UUID is used for the base name. 

    Args:
        url (str): The Spotify playlist URL.
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


def compute_safe_playlist_name(metadata: dict) -> str:
    """Compute the safe playlist name for Rekordbox from the Spotify playlist metadata.

    Args:
        metadata (dict): A dictionary that contains at least the name and description.

    Returns:
        str: The computed playlist name.
    """

    result = None

    name = metadata.get('name')
    description = metadata.get('description')

    if description:
        description = unescape(description)
        d = sanitize_text(description)
        playlist_match = PLAYLIST_DESC_PATTERN.match(d)
        if playlist_match:
            result = playlist_match.group(1)
            result = result.strip()

    if not result:
        result = sanitize_text(name)

    return result


def sanitize_text(text: str) -> str:
    """Remove all symbols and collapse spaces in a text string.

    Args:
        text (str): The text string to clean.

    Returns:
        str: The cleaned text string.
    """

    result = ''.join(
        c for c in text
        if not unicodedata.category(c).startswith(("S", "C"))
    )
    result = re.sub(r"\s+", " ", result).strip()
    return result


def is_valid_spotify_url(url: str) -> bool:
    """Check if the URL is a valid Spotify playlist URL.

    Args:
        url (str): The URL to check.

    Returns:
        bool: If the URL is valid or not.
    """

    if ('open.spotify.com' in url and 'playlist' in url):
        return True
    return False


def is_valid_spotdl_file(filepath: str) -> bool:
    """Check if the path exists and if it's a valid spotdl file.

    Args:
        filepath (str): The file path of the spotdl file.

    Returns:
        bool: If valid or not.
    """

    path = Path(filepath)
    if not path.exists() or path.suffix.lower() != '.spotdl':
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except JSONDecodeError:
        return False

    if not isinstance(data, dict):
        return False
    if data.get('type') != 'sync' or data.get('query') is None or data.get('songs') is None:
        return False

    return True


def search_first_spotdl_file(url: str, ignore_params: bool = True) -> SpotDLFile:
    """Search for the first spotdl file that match the URL in the sync folder.

    Args:
        url (str): The URL used for the search.
        ignore_params (bool, optional): If params in URL should be ignored. Defaults to True.

    Returns:
        str: The filepath of the .spotdl file or `None`
    """

    sync_path = config.get_sync_folder_path()
    spotdl_files = search_spotdl_files(folder_path=sync_path)
    for spotdl_file in spotdl_files:
        if is_actual_sync_file(url, spotdl_file, ignore_params):
            return SpotDLFile.from_filepath(spotdl_file)
    return None


def search_spotdl_files(folder_path: str) -> list[str]:
    """Search for all .spotdl files in the folder.

    Args:
        folder_path (str): The path of folder.

    Returns:
        list[str]: A list .spotdl filepath if found.
    """

    result = []
    for dir_entry in os.scandir(folder_path):
        if dir_entry.is_file() and dir_entry.name.endswith('.spotdl'):
            result.append(dir_entry.path)
    return result


def is_actual_sync_file(url: str, spotdl_file: str, ignore_params: bool = True) -> bool:
    """Check if the SpotDL file is the one corresponding to the URL.

    Args:
        url (str): The URL to use as reference.
        spotdl_file (str): The spotdl file path to check.
        ignore_params (bool, optional): If parameters in URL should be ignored. Defaults to True.

    Returns:
        bool: If the spotdl file is the correct one or `None`
    """

    # TODO: Use SpotDLFile instance instead
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


def sort_songs(songs: list[Song]) -> list[Song]:
    """Sort songs by list position.

    This function sorts the songs based on their list position.
    If the list position is not specified for a song, it will be put at the end of the list.

    This function doesn't change the original list, but uses a copy list instead.

    Args:
        songs (list[Song]): List of songs to be sorted.

    Returns:
        list[Song]: Sorted list of songs.
    """

    sorted_songs = list.copy(songs)
    sorted_songs.sort(key=lambda x: x.list_position or len(songs))
    return sorted_songs


def get_songs_by_playlist_url(url: str, spotdl_file: SpotDLFile, sort: bool = True) -> list[Song]:
    """This function retrieves the songs related to a Spotify playlist that matches the URL.

    Args:
        url (str): URL of the Spotify playlist to retrieve songs from.
        spotdl_file (SpotDLFile): A SpotDLFile instance.
        sort (bool, optional): Whether to sort the songs or not. Defaults to Tru.

    Returns:
        list[Song]: List of songs related to the playlist.
    """

    songs = spotdl_file.songs
    playlist_songs = [song for song in songs if song.list_url == url]
    if sort:
        playlist_songs = sort_songs(playlist_songs)
    return playlist_songs
