from logging import getLogger
from os import linesep
from re import search, MULTILINE
from shlex import split
from subprocess import Popen, PIPE
from sys import platform
from typing import Tuple

from packaging import version

logger = getLogger(__name__)


def run_cmd(cmd: str) -> Tuple[str, str]:
    """
    Run command and return stdout and stderr.

    :param cmd: command to execute
    :return: stdout, stderr
    """
    cmd2exec = split(cmd) if platform == 'linux' else cmd
    logger.debug(f'CMD: {cmd2exec}')
    stdout, stderr = Popen(cmd2exec, stdout=PIPE, stderr=PIPE).communicate()
    out, err = stdout.decode('utf-8'), stderr.decode('utf-8')
    logger.debug(f'StdOut: {out}')
    logger.debug(f'StdErr: {err}')
    return out, err


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
    return False, 'Not tes3cmd'


def is_latest_ver(package: str, current_ver: str) -> Tuple[bool, str]:
    """
    Check if installed package is the latest.

    :param package: package name
    :param current_ver: currently installed version
    """
    extra_data = current_ver
    out, err = run_cmd(f'pip install --dry-run --no-color --timeout 3 --retries 1 --progress-bar off --upgrade {package}')
    match = search(r'Would install\s.*{}-([\d.-]+)'.format(package), out)
    if match:
        extra_data = match.group(1)
        logger.debug(f'New version: {extra_data}')
    match = search(r'no such option:\s(.*)', err)
    if match:
        extra_data = match.group(1)
        logger.warning(f'Version check failed, unknown switch: {extra_data}')
        out, _ = run_cmd('pip list')
        match = search(r'pip\s*([\d.]*)', out)
        if match:
            extra_data = f'unknown switch {extra_data} pip: {match.group(1)}'
            logger.debug(f'Pip version: {match.group(1)}')
    latest = _compare_versions(package, current_ver, extra_data)
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
        logger.info(f'There is new version of {package}: {remote_ver}')
    elif version.parse(remote_ver) <= version.parse(current_ver):
        logger.info(f'{package} is up-to-date version: {current_ver}')
        latest = True
    return latest
