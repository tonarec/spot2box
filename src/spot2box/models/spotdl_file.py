"""
SpotDLFile module for handling spotdl file data.
"""

import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict
from spotdl.types.song import Song

PathLike = Path | str


class SpotDLFileError(Exception):
    """
    Base class for all exceptions related to spotdl files.
    """


@dataclass
class SpotDLFile():
    """
    SpotDLFile class. Contains all the data related to a spotdl file.
    """

    type: str
    query: list[str]
    songs: list[Song]
    path: Path

    @classmethod
    def from_filepath(cls, filepath: PathLike) -> "SpotDLFile":
        """Creates a `SpotDLFile` instance from a filepath.

        Args:
            filepath (PathLike): The filepath of the corresponding JSON file.

        Returns:
            SpotDLFile: The created instance.
        """

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
        except JSONDecodeError as e:
            raise SpotDLFileError(
                "Invalid SpotDL data format for file: {filepath}"
            ) from e

        spotdl = cls.from_dict(file_data, filepath)
        return spotdl

    @classmethod
    def from_dict(cls, data: Dict[str, Any], filepath: PathLike = None) -> "SpotDLFile":
        """Create a `SpotDLFile` instance from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary to be converted.
            filepath (PathLike, optional): The filepath of the corresponding JSON file.
            Used for reload purpose. Defaults to None.

        Returns:
            SpotDLFile: The created instance.
        """

        try:
            spotdl = cls(
                type=data['type'],
                query=data['query'],
                songs=[Song.from_dict(song) for song in data['songs']],
                path=Path(filepath) if filepath else None,
            )
        except TypeError as e:
            raise SpotDLFileError("Invalid data format for SpotDLFile.") from e
        return spotdl

    def update_query(self, url: str):
        """Update the query of the instance. Only one query is allowed per spotdl file, 
        and are most of the time just Spotify URL.

        Args:
            url (str): A spotdl query.
        """

        if len(self.query) == 0:
            self.query = [url]
        elif self.query[0] != url:
            self.query[0] = url

    def reload(self):
        """Reloads the SpotDLFile object fields.

        If the object was created with a filepath,
        it will use the same path to reload data.
        """

        if self.path and self.path.exists():
            new_file = self.from_filepath(self.path)
            self.__dict__.update(new_file.__dict__)
