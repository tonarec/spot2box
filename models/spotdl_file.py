"""
SpotDLFile module for handling spotdl file data.
"""

import json
from pathlib import Path
from typing import Any, Dict, Union

from spotdl.types.song import Song

PathLike = Union[Path, str]


class SpotDLFileError(Exception):
    """
    Base class for all exceptions related to spotdl files.
    """


class SpotDLFile():
    """
    SpotDLFile class. Contains all the informations about a spotdl file.
    """

    type: str
    query: list[str]
    songs: list[Song]
    path: Path

    @classmethod
    def from_filepath(cls, filepath: PathLike) -> "SpotDLFile":
        with open(filepath, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        spotdl = cls.from_dict(file_data, filepath)
        return spotdl

    @classmethod
    def from_dict(cls, data: Dict[str, Any], path: PathLike = None) -> "SpotDLFile":
        spotdl = cls(
            type=data['type'],
            query=data['query'],
            songs=[Song.from_dict(song) for song in data['songs']],
            path=Path(path)
        )
        return spotdl

    def reload(self):
        """Reloads the SpotDLFile fields.

        If the object was created with a filepath,
        it will use the same path to reload data.
        """
        if self.path and self.path.exists():
            new_file = self.from_filepath(self.path)
            self.__dict__.update(new_file.__dict__)
