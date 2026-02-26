"""Utils module for Spotify"""
import re


def remove_intl_from_url(url: str) -> str:
    """Removes the internatial parameter from URL

    Args:
        url (str): The URL to clean

    Returns:
        str: The new URL
    """
    url = re.sub(r"\/intl-\w+\/", "/", url)
    return url
