from logging import getLogger
from os import name
from platform import architecture, uname, python_implementation, python_version
from sys import platform

from mht.log import config_logger

LOG = getLogger(__name__)
config_logger(logger=LOG, verbose=True)
LOG.debug(f'Arch: {name} / {platform} / {" / ".join(architecture())}')
LOG.debug(f'Python: {python_implementation()}-{python_version()}')
LOG.debug(f'{uname()}')
