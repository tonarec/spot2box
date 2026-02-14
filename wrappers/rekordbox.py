"""Module that hanlde a wrapper for Rekordbox"""
import logging
import os
import signal
import time
from pathlib import Path

import psutil
from pyrekordbox import Rekordbox6Database, RekordboxXml, config
from pyrekordbox.db6 import (DjmdAlbum, DjmdArtist, DjmdContent, DjmdGenre,
                             DjmdPlaylist)


class RekordboxWrapper():
    def __init__(self, xml_path: str = None):
        logging.debug('Current loaded configuration')
        for line in config.pformat_config().split('\n'):
            logging.debug(line)

        self._db = Rekordbox6Database()
        self._xml = RekordboxXml(xml_path) if xml_path else None
        self.__detect_rekordbox()

    ############
    # Database
    ############
    def propagate_xml_to_database(self):
        if self.xml is None and self.db is None:
            logging.warning('No XML configuration will be propagated')

    def apply_changes(self):
        self._db.commit()

    ############
    # Playlist
    ############
    def add_track_to_playlist(self, path: str, playlist_name: str, pos: int = None):
        path = Path(path)
        path_string = str(path)

        # Get the track content
        content = self._db.get_content(FolderPath=path_string).first()
        if not content:
            logging.warning('Track path not found: %s', path)
            return

        # Get the playlist
        playlist = self.get_or_create_playlist(playlist_name)

        # Check position
        nbr_tracks = len(playlist.Songs)
        if pos:
            if pos < 1:
                pos = 1
            elif pos >= nbr_tracks:
                pos = nbr_tracks + 1

        # Finally add the track to playlist
        self._db.add_to_playlist(playlist, content, pos)

    def remove_track_from_playlist(self, path: str, playlist_name: str):
        path = Path(path)
        path_string = str(path)

        # Get the track content
        content = self._db.get_content(FolderPath=path_string).first()
        if not content:
            logging.warning('Track path not found: %s', path)
            return

        # Get the playlist
        playlist = self._db.get_playlist(Name=playlist_name).first()
        if not playlist:
            logging.warning('Playlist not found: %s', playlist_name)
            return

        # Check if the track is in the playlist
        song_playlist = self._db.get_playlist_songs(
            ContentID=content.ID,
            PlaylistID=playlist.ID
        ).first()
        if not song_playlist:
            logging.warning(
                'Track %s is not in playlist %s', path, playlist_name
            )
            return

        # Finally remove the track from playlist
        self._db.remove_from_playlist(playlist, song_playlist)

    ############
    # Tracks
    ############
    def add_track_to_database(self, path: str, title: str, artist: str, album: str, genre: str):
        logging.info('Adding track %s to database...', path)

        djm_artist = self.get_or_create_artist(artist)
        djm_album = self.get_or_create_album(album, djm_artist.ID)
        djm_genre = self.get_or_create_genre(genre)

        try:
            content = self._db.add_content(
                path,
                Title=title,
                Artist=djm_artist,
                Album=djm_album,
                Genre=djm_genre
            )
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

        content = self._db.get_content(FolderPath=path_string).first()
        if not content:
            logging.warning('File to remove not found: %s', path)
            return

        self._db.delete(content)
        logging.info('Track removed from database: %s', path)

    ############
    # Content
    ############
    def get_or_create_playlist(self, name: str) -> DjmdPlaylist:
        playlist = self._db.get_playlist(Name=name).first()
        if playlist is not None:
            logging.debug(
                'Found playlist %s (%s) in database', name, playlist.ID
            )
            return playlist

        playlist = self._db.create_playlist(name)
        logging.debug(
            'Created playlist %s (%s) in database', name, playlist.ID
        )
        return playlist

    def get_or_create_artist(self, name: str) -> DjmdArtist:
        artist = self._db.get_artist(Name=name).first()
        if artist is not None:
            logging.debug('Found artist %s (%s) in database', name, artist.ID)
            return artist

        artist = self._db.add_artist(name)
        logging.debug('Created artist %s (%s) in database', name, artist.ID)
        return artist

    def get_or_create_album(self, name: str, artist_id: str) -> DjmdAlbum:
        album = self._db.get_album(Name=name, AlbumArtistID=artist_id).first()
        if album is not None:
            logging.debug('Found album %s (%s) in database', name, album.ID)
            return album

        album = self._db.add_album(name, artist_id)
        logging.debug('Created album %s (%s) in database', name, album.ID)
        return album

    def get_or_create_genre(self, name: str) -> DjmdGenre:
        genre = self._db.get_genre(Name=name).first()
        if genre is not None:
            logging.debug('Found genre %s (%s) in database', name, genre.ID)
            return genre

        genre = self._db.add_genre(name)
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

    def print_playlists(self, expand=False):
        playlists = self._db.get_playlist()
        for playlist in playlists:
            logging.info('Playlist: %s (%s)', playlist.Name, playlist.ID)
            if expand:
                songs = playlist.Songs
                for song in songs:
                    content = song.Content
                    logging.debug(
                        '\t%s - %s', content.ArtistName, content.Title
                    )

    def print_artists(self):
        artists: list[DjmdArtist] = self._db.get_artist()
        for artist in artists:
            logging.debug('Artist: %s (%s)', artist.Name, artist.ID)

    def print_albums(self):
        albums: list[DjmdArtist] = self._db.get_album()
        for album in albums:
            logging.debug('Album: %s (%s)', album.Name, album.ID)
