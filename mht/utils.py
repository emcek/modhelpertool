from re import search, MULTILINE
from typing import Tuple


def parse_cleaning(out: str, err: str, mod_filename: str) -> Tuple[bool, str]:  # type: ignore
    """
    Parse output of cleaning command printout.

    :param out: Command STANDARD OUTPUT
    :param err: Command STANDARD ERROR
    :param mod_filename: Mod filename
    :return: Result and reason
    """
    ceases = {
        1: {'args': (r'^\[ERROR \({}\): Master: (.* not found) in <DATADIR>]$'.format(mod_filename), err, MULTILINE),
            'result': False},
        2: {'args': (r'^{} was (not modified)$'.format(mod_filename), out, MULTILINE),
            'result': False},
        3: {'args': (r'Output (saved) in: "1/{}"\nOriginal unaltered: "{}"'.format(mod_filename, mod_filename), out, MULTILINE),
            'result': True},
    }
    for data in ceases.values():
        match = search(*data['args'])  # type: ignore
        if match:
            return data['result'], match.group(1)  # type: ignore
