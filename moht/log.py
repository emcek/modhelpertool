from datetime import datetime
from logging import DEBUG, StreamHandler, INFO, Formatter, WARNING, getLogger
from logging.handlers import RotatingFileHandler
from os import path
from tempfile import gettempdir


__logger_configured = False


def _configure_logger(verbose: int, quiet: bool) -> None:
    root_logger = getLogger('moht')
    root_logger.setLevel(DEBUG)
    file_hand = RotatingFileHandler(filename=path.join(gettempdir(), 'moht.log'), mode='a', encoding='utf-8', maxBytes=5 * 1024 * 1024, backupCount=1)
    file_hand.setLevel(DEBUG)
    file_hand.setFormatter(Formatter('%(asctime)s | %(name)-17s | %(levelname)-7s | %(threadName)-10s | %(message)s / %(funcName)s:%(lineno)d'))
    root_logger.addHandler(file_hand)
    header = '#' * 60
    root_logger.debug(f'\n{header}\nStart session: {datetime.now()}\n{header}')

    if not quiet:
        stream_hand = StreamHandler()
        if verbose == 0:
            stream_hand.setLevel(WARNING)
        if verbose == 1:
            stream_hand.setLevel(INFO)
        if verbose >= 2:
            stream_hand.setLevel(DEBUG)
        stream_hand.setFormatter(Formatter('%(levelname)-7s | %(message)s'))
        root_logger = getLogger('moht')
        root_logger.addHandler(stream_hand)

    global __logger_configured
    __logger_configured = True


def config_logger(verbose: int, quiet: bool) -> None:
    """
    Configure global logger, handlers and set formatters.

    :param verbose: increase verbosity with increment of integer
    :param quiet: turn on/off quiet mode
    """
    if not __logger_configured:
        _configure_logger(verbose, quiet)
