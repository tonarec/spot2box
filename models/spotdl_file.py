"""
SpotDLFile module for handling spotdl file data.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict

from spotdl.types.song import Song


class SpotDLFileError(Exception):
    """
    Base class for all exceptions related to spotdl files.
    """


@dataclass(frozen=True)
class SpotDLFile():
    """
    SpotDLFile class. Contains all the informations about a spotdl file.
    """

    type: str
    query: list[str]
    songs: list[Song]

    @classmethod
    def from_filepath(cls, filepath: str) -> "SpotDLFile":
        with open(filepath, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        spotdl = cls.from_dict(file_data)
        return spotdl

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpotDLFile":
        spotdl = cls(
            type=data['type'],
            query=data['query'],
            songs=[Song.from_dict(song) for song in data['songs']]
        )
        return spotdl
