"""Module that hanlde a wrapper for Rekordbox"""
from pyrekordbox import show_config, Rekordbox6Database<

import logging


class RekordboxWrapper():
    def __init__(self, path: str):
        logging.info('Current loaded configuration')
        show_config()
        self.db = Rekordbox6Database()

    def print_playlists(self):
        playlists = self.db.get_playlist()
        for playlist in playlists:
            logging.debug('Playlist: %s' ,playlist.Name)
            songs = playlist.Songs
            for song in songs:
                content = song.Content
                logging.debug('\t%s - %s', content.ArtistName, content.Title)
