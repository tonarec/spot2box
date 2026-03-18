"""Module that handle a wrapper for Rekordbox"""

import logging
import os
import signal
import time
from collections import Counter
from pathlib import Path
from typing import Union

import psutil
from pyrekordbox import MasterDatabase, RekordboxXml
from pyrekordbox.config import pformat_config
from pyrekordbox.masterdb import (DjmdAlbum, DjmdArtist, DjmdContent,
                                  DjmdGenre, DjmdPlaylist, DjmdSongPlaylist)

from spot2box.core.config import Spot2BoxConfig

PathLike = Union[Path, str]
PlaylistLike = Union[DjmdPlaylist, str]
ContentLike = Union[DjmdContent, PathLike]


class RekordboxWrapper():
    def __init__(self, config: Spot2BoxConfig):
        logging.debug('Current loaded configuration')
        for line in pformat_config().split('\n'):
            logging.debug(line)

        xml_path = config.rekordbox_xml
        force_kill = config.force_kill

        self._config = config
        self._db = MasterDatabase()
        self._xml = RekordboxXml(xml_path) if xml_path else None
        self._detect_rekordbox(force_kill)

    def propagate_xml_to_database(self):
        # TODO: Check if database is loaded instead
        if self._xml is None and self._db is None:
            logging.warning('No XML configuration will be propagated')

    def commit_changes(self):
        """Apply all pending changes to the database."""

        self._db.commit()

    def sync_playlist(self, playlist: PlaylistLike, tracks: list[PathLike]):
        """Synchronize the playlist with a list of tracks.

        This method search for tracks to add/remove in the playlist,
        and make the exact same playlist from the list. The list of tracks
        must be existing filepaths.

        Args:
            playlist (PlaylistLike): _description_
            tracks (list[PathLike]): _description_
        """

        # Get the playlist
        playlist = self.get_or_create_playlist(playlist)
        playlist_songs: list[DjmdSongPlaylist] = playlist.Songs
        playlist_contents: list[DjmdContent] = [
            psong.Content for psong in playlist_songs]
        playlist_paths = [content.FolderPath for content in playlist_contents]

        logging.info('Syncing playlist "%s" into Rekordbox...', playlist.Name)

        track_paths = [Path(track).as_posix() for track in tracks]

        # Remove tracks not present in list
        contents_to_remove = []
        if not self._config.add_only:
            playlist_counter = Counter(playlist_paths)
            track_counter = Counter(track_paths)
            contents_to_remove = playlist_counter - track_counter

        # Add new tracks to playlist
        contents_to_add = []
        for track_path in track_paths:
            if not track_path in playlist_paths:
                contents_to_add.append(track_path)

        # Proceed playlist update
        for content in contents_to_remove:
            self.remove_track_from_playlist(
                track=content, playlist=playlist, remove_occurences=False)

            # Remove the track if no longer in playlists
            if self._config.delete_standalone_track:
                related_playlists = self.get_track_related_playlists(content)
                if len(related_playlists) == 0:
                    self.remove_track_from_database(content)

        for content in contents_to_add:
            self.add_track_to_playlist(path=content, playlist_name=playlist)

        # Reload playlist instance
        self.commit_changes()
        if len(track_paths) != len(playlist.Songs):
            logging.error(
                'Something went wrong when updating playlist %s', playlist.Name
            )
            return

        # Sort playlist according to the list order
        if self._config.sort_playlist:
            for index, track_path in enumerate(track_paths):
                # Get the track in the playlist
                current_content: DjmdContent = self._db.get_content(
                    FolderPath=track_path).one()
                current_psong: DjmdSongPlaylist = self._db.get_playlist_songs(
                    PlaylistID=playlist.ID,
                    ContentID=current_content.ID).one()

                # Check the track position
                trackpos = index + 1
                if current_psong.TrackNo != trackpos:
                    # Move the track if the current index didn't match
                    self._db.move_song_in_playlist(
                        playlist=playlist,
                        song=current_psong,
                        new_track_no=trackpos
                    )

        self.commit_changes()
        logging.info('Playlist "%s" synced!', playlist.Name)
        logging.debug('    Tracks added in playlist: %d', len(contents_to_add))
        logging.debug('    Tracks removed from playlist: %d',
                      len(contents_to_remove))

    def add_track_to_playlist(self, path: str, playlist_name: str, pos: int = None):
        """Add a track to a playlist. The playlist will be created if does not exists in database.

        Args:
            path (str): _description_
            playlist_name (str): _description_
            pos (int, optional): _description_. Defaults to None.
        """

        # Get the track content
        content = self.get_track_in_database(path)
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

    def remove_track_from_playlist(self, track: ContentLike, playlist: PlaylistLike, remove_occurences=True):
        """This method removes all the occurences of the track in the playlist.

        Args:
            track (ContentLike): The `DjmContent` or a filepath to the track
            playlist (PlaylistLike): The `DjmPlaylist` or the playlist name
        """

        # Get the track content
        content = self._get_actual_content(track)
        if not content:
            logging.warning('Track path not found: %s', track)
            return

        # Get the playlist
        plist = self._get_actual_playlist(playlist)
        if not plist:
            logging.warning('Playlist not found: %s', playlist)
            return

        # Check if the track is in the playlist
        result = self._db.get_playlist_songs(
            PlaylistID=plist.ID,
            ContentID=content.ID
        )

        # Finally remove the track from playlist
        playlist_songs = result.all()
        if len(playlist_songs) == 0:
            logging.warning(
                'Track %s is not in playlist %s', content.FolderPath, playlist.Name
            )
            return

        nb_songs = len(playlist_songs) if remove_occurences else 1
        for index in range(nb_songs):
            psong = playlist_songs[index]
            self._db.remove_from_playlist(plist, psong)

    def get_track_related_playlists(self, track: ContentLike) -> list[DjmdPlaylist]:

        playlists: set[DjmdPlaylist] = set()

        # Get the track content
        content = self._get_actual_content(track)
        if not content:
            logging.warning('Track path not found: %s', track)
            return

        # Check if the track is in the playlist
        result = self._db.get_playlist_songs(
            ContentID=content.ID
        )

        # Get playlist for each song playlist
        for psong in result.all():
            playlists.add(psong.Playlist)
        return playlists

    def get_track_in_database(self, path: PathLike) -> DjmdContent:
        """Retrieve the first track in Database that match the path or `None`.
        The path will be normalized to a POSIX-like representation to fit the Rekordbox Database.

        Args:
            path (str): The path to search for

        Returns:
            DjmdContent: The content for this path
        """
        content = self._get_actual_content(path)
        if not content:
            logging.warning('Track path not found: %s', path)
            return None
        return content

    def add_track_to_database(self, path: PathLike, title: str, artist: str, album: str, genre: str):

        path = Path(path).as_posix()
        logging.info('Adding track %s to database...', path)

        djm_artist = self.get_or_create_artist(artist)
        djm_album = self.get_or_create_album(album, djm_artist.ID)
        djm_genre = self.get_or_create_genre(genre) if genre else None

        try:
            content = self._db.add_content(
                path=path,
                Title=title,
                Artist=djm_artist,
                Album=djm_album,
                Genre=djm_genre
            )
        except ValueError:
            logging.debug('Track %s already exists in database', path)
            return

        logging.info('Added new track to database: %s', path)
        logging.debug('  Title: %s', content.Title)
        logging.debug('  Artist: %s', content.ArtistName)
        logging.debug('  Genre: %s', content.Genre)

    def remove_track_from_database(self, track: ContentLike):
        content = self._get_actual_content(track)
        if not content:
            logging.warning('File to remove not found: %s', track)
            return

        self._db.delete(content)
        logging.info('Track removed from database: %s', content.FolderPath)

    def _get_actual_playlist(self, playlist: PlaylistLike) -> DjmdPlaylist:
        if isinstance(playlist, str):
            playlist = self._db.get_playlist(Name=playlist).first()
        return playlist

    def _get_actual_content(self, content: ContentLike) -> DjmdContent:
        if isinstance(content, PathLike):
            path = Path(content).as_posix()
            content = self._db.get_content(FolderPath=path).first()
        return content

    def get_or_create_playlist(self, name: str) -> DjmdPlaylist:
        playlist = self._get_actual_playlist(name)
        if playlist:
            logging.debug(
                'Found playlist %s (%s) in database', playlist.Name, playlist.ID
            )
            return playlist

        playlist = self._db.create_playlist(name)
        logging.info(
            'Created playlist %s (%s) in database', name, playlist.ID
        )
        return playlist

    def get_or_create_artist(self, name: str) -> DjmdArtist:
        artist = self._db.get_artist(Name=name).first()
        if artist is not None:
            logging.debug('Found artist %s (%s) in database', name, artist.ID)
            return artist

        artist = self._db.add_artist(name)
        logging.info('Created artist %s (%s) in database', name, artist.ID)
        return artist

    def get_or_create_album(self, name: str, artist_id: str) -> DjmdAlbum:
        album = self._db.get_album(Name=name, AlbumArtistID=artist_id).first()
        if album is not None:
            logging.debug('Found album %s (%s) in database', name, album.ID)
            return album

        album = self._db.add_album(name, artist_id)
        logging.info('Created album %s (%s) in database', name, album.ID)
        return album

    def get_or_create_genre(self, name: str) -> DjmdGenre:
        genre = self._db.get_genre(Name=name).first()
        if genre is not None:
            logging.debug('Found genre %s (%s) in database', name, genre.ID)
            return genre

        genre = self._db.add_genre(name)
        logging.info('Created genre %s (%s) in database', name, genre.ID)
        return genre

    def _get_pids(self) -> list[int]:
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

    def _detect_rekordbox(self, force_kill=False):
        """Detect Rekordbox process if exists and block the application until closed."""
        pids = self._get_pids()
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
            pids = self._get_pids()
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
                    content: DjmdContent = song.Content
                    logging.debug(
                        '\t%s - %s (%s)', content.ArtistName, content.Title, content.FolderPath
                    )

    def print_artists(self):
        artists: list[DjmdArtist] = self._db.get_artist()
        for artist in artists:
            logging.debug('Artist: %s (%s)', artist.Name, artist.ID)

    def print_albums(self):
        albums: list[DjmdArtist] = self._db.get_album()
        for album in albums:
            logging.debug('Album: %s (%s)', album.Name, album.ID)
