"""Module that initialize the logger"""
import logging
import sys
from datetime import datetime
from utils import info


def init_logger(level: int = logging.INFO):
    """Initialize the logger.

    Args:
        folder_path (str): The path of the logs folder
    """
    filename = __compute_filename()
    filepath = './logs/' + filename

    logging.basicConfig(level=level,
                        format='%(asctime)s,%(msecs)03d [%(module)8s] %(levelname)7s - %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S",
                        handlers=[
                            logging.FileHandler(filepath),
                            logging.StreamHandler(sys.stdout)
                        ])

    app_name = info.get_app_name()
    version = info.get_version()
    author = info.get_author()
    logging.info('%s v%s (%s)', app_name, version, author)


def __compute_filename():
    """Compute a filename for the log file with the date and time of creation.

    Returns:
        str: Filename formatted as 'log_YYYYMMDD_HHMMSS.log'
    """
    log_filename = 'log_' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.log'
    return log_filename
