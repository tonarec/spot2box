"""Module that hanlde a wrapper for Rekordbox"""
import sys
import os
import pyrekordbox
from pyrekordbox import Rekordbox6Database, RekordboxXml
from pyrekordbox.db6 import DjmdPlaylist, DjmdContent, DjmdArtist, DjmdGenre, DjmdAlbum
from pyrekordbox import utils

import logging


class RekordboxWrapper():
    def __init__(self, xml_path: str = None):
        logging.info('Current loaded configuration')
        pyrekordbox.show_config()
        self.db = Rekordbox6Database()
        self.xml = RekordboxXml(xml_path)
        self.__detect_rekordbox()

    ############
    # Database
    ############
    def __detect_rekordbox(self):
        """Detect Rekordbox process if exists and block the application until closed."""
        pid = utils.get_rekordbox_pid()
        while pid != 0:
            logging.warning(
                'Rekordbox process (%d) is running! Please close Rekordbox to continue...', pid)

    def propagate_xml_to_database(self):
        if self.xml is None and self.db is None:
            logging.warning('No XML configuration will be propagated')

    def apply_changes(self):
        self.db.commit()

    ############
    # Playlist
    ############
    def get_playlists(self, filter: str = None) -> list[DjmdPlaylist]:
        if filter is not None:
            return self.db.get_playlist(Name=filter)
        return self.db.get_playlist()

    def get_or_create_playlist(self, name: str) -> DjmdPlaylist:
        playlist = self.db.get_playlist(Name=name)
        result = playlist.first()
        if result is not None:
            return result

        playlist = self.db.create_playlist(name)
        return playlist

    ############
    # Tracks
    ############
    def add_track_to_database(self, path: str, title: str, artist: str, album: str, album_artist: str, genre: str):
        djm_artist = self.get_or_create_artist(artist)

        content = self.db.add_content(path,
                                      Title=title,
                                      Artist=djm_artist)

        logging.info('Added new track to database: %s', path)
        logging.debug('\tTitle: %s', content.Title)
        logging.debug('\tArtist: %s', content.ArtistName)
        logging.debug('\tGenre: %s', content.Genre)

    def remove_track_from_database(self, uri: str):
        pass

    def append_track_to_playlist(self, uri: str, playlist_name: str):
        pass

    def insert_track_to_playlist(self, uri: str, playlist_name: str):
        pass

    ############
    # Artist
    ############
    def get_or_create_artist(self, name: str) -> DjmdArtist:
        artist = self.db.get_artist(Name=name)
        result = artist.first()
        if result is not None:
            return result

        artist = self.db.add_artist(name)
        return artist

    ############
    # Utils
    ############
    def print_playlists(self):
        playlists = self.get_playlists()
        for playlist in playlists:
            logging.info('Playlist: %s', playlist.Name)
            songs = playlist.Songs
            for song in songs:
                content = song.Content
                logging.info('\t%s - %s', content.ArtistName, content.Title)
