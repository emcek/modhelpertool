from itertools import chain
from logging import getLogger
from os import linesep, path, sep, walk, remove
from pathlib import Path
from re import findall, search, MULTILINE
from shlex import split
from shutil import rmtree, copy2
from subprocess import Popen, PIPE
from sys import platform
from typing import Tuple, Union, List, Set

from packaging import version

from moht import PLUGINS2CLEAN

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


def parse_cleaning(out: str, err: str, mod_filename: str) -> Tuple[bool, str]:
    """
    Parse output of cleaning command printout.

    :param out: Command STANDARD OUTPUT
    :param err: Command STANDARD ERROR
    :param mod_filename: Mod filename
    :return: Result and reason
    """
    result = False, 'Not tes3cmd'
    ceases = {
        1: {'args': (r'\[ERROR \({}\): Master: (.* not found) in <DATADIR>]'.format(mod_filename), err, MULTILINE),
            'result': False,
            'join': True},
        2: {'args': (r'{} was (not modified)'.format(mod_filename), out, MULTILINE),
            'result': False,
            'join': False},
        3: {'args': (r'Output (saved) in: "1/{}"{}Original unaltered: "{}"'.format(mod_filename, linesep, mod_filename), out, MULTILINE),
            'result': True,
            'join': False},
        4: {'args': (r'Can\'t locate Config/IniFiles.pm in @INC \(you may need to install the (Config::IniFiles module)\)', err, MULTILINE),
            'result': False,
            'join': False},
        5: {'args': (r'(Usage): tes3cmd COMMAND OPTIONS plugin...', err, MULTILINE),
            'result': True,
            'join': False},
    }
    for data in ceases.values():
        match = findall(*data['args'])  # type: ignore
        if match and data['join']:
            result = bool(data['result']), '**'.join(match)
            break
        elif match and not data['join']:
            result = bool(data['result']), str(match[0])
            break
    return result


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
        logger.debug(f'Latest available version: {extra_data}')
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


def here(filename: str) -> str:
    """
    Absolute path to directory contains filename.

    :param filename:
    :return: path to directory as string
    """
    return path.abspath(path.dirname(filename))


def extract_filename(file_path: Union[str, Path]) -> str:
    """
    Extract filename from path.

    :param file_path: string or path like object
    :return: last element of path
    """
    return str(file_path).split(sep)[-1]


def get_all_plugins(mods_dir: str) -> List[Path]:
    """
    Get list of absolute paths  for all plugins in mods_dir directory.

    :param mods_dir: rood directory of mods
    :return: List of Path objects
    """
    return [Path(path.join(root, filename))
            for root, _, files in walk(mods_dir)
            for filename in files
            if filename.lower().endswith('.esp') or filename.lower().endswith('.esm')]


def get_plugins_to_clean(plugins: List[Path]) -> List[Path]:
    """
    Get list of plugins to clean.

    :param plugins: list of plugins
    :return: list of plugins to clean
    """
    return [plugin_file for plugin_file in plugins if extract_filename(plugin_file) in PLUGINS2CLEAN]


def get_required_esm(plugins: List[Path]) -> Set[str]:
    """
    Get set of required esm files.

    :param plugins:
    :return:
    """
    return set(chain.from_iterable([PLUGINS2CLEAN[extract_filename(plugin)] for plugin in plugins]))


def rm_dirs_with_subdirs(dir_path: str, subdirs: List[str]) -> None:
    """
    Remove directories with specific subdirectories.

    :param dir_path: root directory
    :param subdirs: list of subdirectories of root to remove
    """
    for directory in [path.join(dir_path, subdir) for subdir in subdirs]:
        logger.debug(f'Remove: {directory}')
        rmtree(directory, ignore_errors=True)


def find_missing_esm(dir_path: str, data_files: str, esm_files: Set[str]) -> List[Path]:
    """
    Find missing esm files in Morrowind Data Files folder.

    :param dir_path: directory path of mods
    :param data_files: Morrowind Data Files directory
    :param esm_files: set of esm file names
    :return: list of files
    """
    in_datafiles = {filename
                    for _, _, files in walk(data_files)
                    for filename in files
                    if filename in esm_files}
    missing_files = set(esm_files) - in_datafiles
    file_list = [Path(path.join(root, filename))
                 for root, _, files in walk(dir_path)
                 for filename in files
                 if filename in missing_files]
    return file_list


def copy_filelist(file_list: List[Path], dest_dir: str) -> None:
    """
    Copy files from file_list to dest_dir.

    :param file_list: list of files to copy
    :param dest_dir: destination directory
    """
    for file_path in file_list:
        logger.debug(f'Copy: {file_path} -> {dest_dir}')
        copy2(file_path, dest_dir)


def rm_copied_extra_esm(esm: List[Path], data_files: str) -> None:
    """
    Remove extra esm files from Morrowind Data Files folder.

    :param esm: list of esm files
    :param data_files: Morrowind Data Files directory
    """
    for esm_file in esm:
        esm_path = path.join(data_files, extract_filename(esm_file))
        try:
            remove(esm_path)
        except FileNotFoundError:
            logger.debug(f'File not found: {esm_path}')
        else:
            logger.debug(f'Remove: {esm_path}')
