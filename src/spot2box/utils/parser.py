"""
Module that initialize the parser.
"""

from argparse import ArgumentParser, Namespace


def create_parser() -> ArgumentParser:
    """Creates the parser for the command line interface.

    Returns:
        ArgumentParser: The parser object.
    """

    parser = ArgumentParser(
        prog='Spot2Box - Spotify to Rekordbox Playlist Manager',
        description='Unlock the potential of your Spotify playlists in Rekordbox.')

    # Main options
    main_options = parser.add_argument_group('Main options')
    main_options.add_argument('-o', '--output',
                              type=str,
                              help='Output folder to download tracks.')

    main_options.add_argument('-s', '--save',
                              dest='save_config',
                              action='store_true',
                              help='Save current configuration into application folder.')

    # Rekordbox options
    rekordbox_options = parser.add_argument_group('Rekordbox options')
    rekordbox_options.add_argument('--rekordbox-xml',
                                   type=str,
                                   help='A rekordbox.xml file to update.')

    rekordbox_options.add_argument('--rekordbox-path',
                                   type=str,
                                   help='The Rekordbox installation path.')

    rekordbox_options.add_argument('--add-only',
                                   action='store_true',
                                   help='Only add new tracks in Rekordbox playlists.')

    rekordbox_options.add_argument('--allow-duplicate',
                                   action='store_true',
                                   help='Allow tracks duplication in Rekordbox playlists.')

    rekordbox_options.add_argument('--delete-standalone',
                                   dest='delete_standalone_track',
                                   action='store_true',
                                   help='Remove tracks in database that are no longer in a playlist.')

    rekordbox_options.add_argument('--force-kill',
                                   action='store_true',
                                   help='Force kill Rekordbox if running.')

    rekordbox_options.add_argument('--open',
                                   dest='open_rekordbox',
                                   action='store_true',
                                   help='Open Rekordbox at the end.')

    # Spotify options
    spotify_options = parser.add_argument_group('Spotify options')
    spotify_options.add_argument('-u', '--url',
                                 type=str,
                                 dest='urls',
                                 action='append',
                                 help='Spotify Playlist URLs to process.')

    spotify_options.add_argument('-f', '--spotdl-file',
                                 type=str,
                                 dest='spotdl_files',
                                 action='append',
                                 help='SpotDL files to use as inputs.')

    spotify_options.add_argument('--spotify-client',
                                 type=str,
                                 help='The Spotify Client ID to use for the API.')

    spotify_options.add_argument('--spotify-secret',
                                 type=str,
                                 help='The Spotify Secret to use for the API.')

    return parser


def parse_args() -> Namespace:
    """Parse the command line arguments and return a Namespace object.

    Returns:
        Namespace: A Namespace object with the parsed arguments.
    """

    parser = create_parser()
    args = parser.parse_args()
    return args
