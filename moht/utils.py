from logging import getLogger
from os import linesep
from re import search, MULTILINE
from shlex import split
from subprocess import Popen, PIPE
from sys import platform
from typing import Tuple

from packaging import version

LOG = getLogger(__name__)


def parse_cleaning(out: str, err: str, mod_filename: str) -> Tuple[bool, str]:  # type: ignore
    """
    Parse output of cleaning command printout.

    :param out: Command STANDARD OUTPUT
    :param err: Command STANDARD ERROR
    :param mod_filename: Mod filename
    :return: Result and reason
    """
    ceases = {
        1: {'args': (r'\[ERROR \({}\): Master: (.* not found) in <DATADIR>]'.format(mod_filename), err, MULTILINE),
            'result': False},
        2: {'args': (r'{} was (not modified)'.format(mod_filename), out, MULTILINE),
            'result': False},
        3: {'args': (r'Output (saved) in: "1/{}"{}Original unaltered: "{}"'.format(mod_filename, linesep, mod_filename), out, MULTILINE),
            'result': True},
        4: {'args': (r'Can\'t locate Config/IniFiles.pm in @INC \(you may need to install the (Config::IniFiles module)\)', err, MULTILINE),
            'result': False},
        5: {'args': (r'(Usage): tes3cmd COMMAND OPTIONS plugin...', err, MULTILINE),
            'result': True},
    }
    for data in ceases.values():
        match = search(*data['args'])  # type: ignore
        if match:
            return data['result'], match.group(1)  # type: ignore


def check_new_ver(package: str, current_ver: str) -> Tuple[bool, str]:
    """
    Check if there is new version of package.

    :param package:
    :param current_ver:
    """
    latest, extra_data = False, ''
    cmd_str = f'pip install --dry-run --no-color --timeout 3 --retries 1 --progress-bar off --upgrade tox==3.25.1 {package}==0.37.1'
    cmd = split(cmd_str) if platform == 'linux' else cmd_str
    LOG.debug(f'CMD: {cmd}')
    stdout, stderr = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    out, err = stdout.decode('utf-8'), stderr.decode('utf-8')
    LOG.debug(f'Out: {out}')
    LOG.debug(f'Err: {err}')
    match = search(r'Would install\s.*\s{}-([\d.-]+)'.format(package), out)
    if match:
        extra_data = match.group(1)
        LOG.debug(f'New version: {extra_data}')
        latest = _compare_versions(package, current_ver, extra_data)
    match = search(r'no such option:\s(.*)', err)
    if match:
        extra_data = match.group(1)
        LOG.warning(f'Unknown option: {extra_data}')
        # todo: check version of pip and return as extra_data
    return latest, extra_data


def _compare_versions(package: str, current_ver: str, remote_ver: str) -> bool:
    """
    Compare versions.

    :param package:
    :param current_ver:
    :param remote_ver:
    :return:
    """
    latest = False
    if version.parse(remote_ver) > version.parse(current_ver):
        LOG.info(f'There is new version of {package}: {remote_ver}')
    elif version.parse(remote_ver) <= version.parse(current_ver):
        LOG.info(f'{package} is up-to-date version: {current_ver}')
        latest = True
    return latest
