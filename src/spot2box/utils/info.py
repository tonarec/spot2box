"""Module that handle info of the application"""

import json
import logging

INFO_FILENAME = 'info.json'


def __load_info() -> dict:
    """Load the info object

    Returns:
        dict: The info loaded. Returns None is not found
    """
    try:
        with open(INFO_FILENAME, 'r', encoding='utf-8') as raw:
            return json.load(raw)
    except FileNotFoundError:
        logging.warning('Not info file found!')
        return None


def __get_info(name: str) -> str:
    if info is None:
        return None
    return info[name]


def get_app_name() -> str:
    """Get the application's name

    Returns:
        str: The application's name
    """
    return __get_info('app_name')


def get_author() -> str:
    """Get the author's name

    Returns:
        str: The author's name
    """
    return __get_info('author')


def get_version() -> str:
    """Get the version of the application

    Returns:
        str: The version number
    """
    return __get_info('version')


info = __load_info()
