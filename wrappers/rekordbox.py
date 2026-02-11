"""Module that hanlde a wrapper for Rekordbox"""
import logging
import os
import signal
import time
from pathlib import Path

import psutil
import pyrekordbox
from pyrekordbox import Rekordbox6Database, RekordboxXml, utils
from pyrekordbox.db6 import (DjmdAlbum, DjmdArtist, DjmdContent, DjmdGenre,
                             DjmdPlaylist)


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

    def append_track_to_playlist(self, uri: str, playlist_name: str):
        pass

    def insert_track_to_playlist(self, uri: str, playlist_name: str):
        pass

    ############
    # Tracks
    ############
    def add_track_to_database(self, path: str, title: str, artist: str, album: str, genre: str):
        logging.info('Adding track %s to database', path)

        djm_artist = self.get_or_create_artist(artist)
        djm_album = self.get_or_create_album(album, djm_artist.ID)
        djm_genre = self.get_or_create_genre(genre)

        try:
            content = self.db.add_content(path,
                                          Title=title,
                                          Artist=djm_artist,
                                          Album=djm_album,
                                          Genre=djm_genre)
        except ValueError:
            logging.info('Track already exists in database')
            return

        logging.info('Added new track to database: %s', path)
        logging.debug('  Title: %s', content.Title)
        logging.debug('  Artist: %s', content.ArtistName)
        logging.debug('  Genre: %s', content.Genre)

    def remove_track_from_database(self, path: str):
        path = Path(path)
        path_string = str(path)

        content = self.db.get_content(FolderPath=path_string)
        result = content.first()
        if not result:
            logging.warning('File to remove not found: %s', path)
            return

        self.db.delete(result)
        logging.info('Track removed from database: %s', path)

    ############
    # Content
    ############
    def get_or_create_playlist(self, name: str) -> DjmdPlaylist:
        playlist = self.db.get_playlist(Name=name)
        result = playlist.first()
        if result is not None:
            logging.debug('Found playlist %s (%s) in database',
                          name, result.ID)
            return result

        playlist = self.db.create_playlist(name)
        logging.debug('Created playlist %s (%s) in database',
                      name, playlist.ID)
        return playlist

    def get_or_create_artist(self, name: str) -> DjmdArtist:
        artist = self.db.get_artist(Name=name)
        result = artist.first()
        if result is not None:
            logging.debug('Found artist %s (%s) in database', name, result.ID)
            return result

        artist = self.db.add_artist(name)
        logging.debug('Created artist %s (%s) in database', name, artist.ID)
        return artist

    def get_or_create_album(self, name: str, artist_id: str) -> DjmdAlbum:
        album = self.db.get_album(Name=name, AlbumArtistID=artist_id)
        result = album.first()
        if result is not None:
            logging.debug('Found album %s (%s) in database', name, result.ID)
            return result

        album = self.db.add_album(name, artist_id)
        logging.debug('Created album %s (%s) in database', name, album.ID)
        return album

    def get_or_create_genre(self, name: str) -> DjmdGenre:
        genre = self.db.get_genre(Name=name)
        result = genre.first()
        if result is not None:
            logging.debug('Found genre %s (%s) in database', name, result.ID)
            return result

        genre = self.db.add_genre(name)
        logging.debug('Created genre %s (%s) in database', name, genre.ID)
        return genre

    ############
    # Utils
    ############
    def __get_pids(self) -> list[int]:
        """Get a list of running pids"""
        pids = []
        for proc in psutil.process_iter():
            try:
                proc_name = os.path.splitext(proc.name())[0]
                if proc_name.lower().startswith('rekordbox'):
                    pid = proc.pid
                    pids.append(pid)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        return pids

    def __detect_rekordbox(self, force_kill=False):
        """Detect Rekordbox process if exists and block the application until closed."""
        pids = self.__get_pids()
        if not pids:
            return

        logging.warning('Rekordbox is running!')

        if force_kill:
            logging.info('Shutting down Rekordbox process and agent...')
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

        logging.info('Waiting for Rekordbox to be closed...')
        while True:
            pids = self.__get_pids()
            if not pids:
                logging.info('All Rekordbox processes closed.')
                return
            time.sleep(2)

    def print_playlists(self):
        playlists = self.get_playlists()
        for playlist in playlists:
            logging.info('Playlist: %s (%s)', playlist.Name, playlist.ID)
            songs = playlist.Songs
            for song in songs:
                content = song.Content
                logging.info('\t%s - %s', content.ArtistName, content.Title)

    def print_artists(self):
        artists: list[DjmdArtist] = self.db.get_artist()
        for artist in artists:
            logging.info('Artist: %s (%s)', artist.Name, artist.ID)
