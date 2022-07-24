import re
from typing import Tuple


def parse_cleaning(out: str, err: str, mod_filename: str) -> Tuple[bool, str]:
    """
    Parse output of cleaning command printout.

    :param out: Command STANDARD OUTPUT
    :param err: Command STANDARD ERROR
    :param mod_filename: Mod filename
    :return: Result and reason
    """
    ceases = {
        1: {'args': (r'^\[ERROR \({}\): Master: (.* not found) in <DATADIR>]$'.format(mod_filename), err, re.MULTILINE),
            'result': False},
        2: {'args': (r'^{} was (not modified)$'.format(mod_filename), out, re.MULTILINE),
            'result': False},
        3: {'args': (r'Output (saved) in: "1/{}"\nOriginal unaltered: "{}"'.format(mod_filename, mod_filename), out, re.MULTILINE),
            'result': True},
    }
    for data in ceases.values():
        match = re.search(*data['args'])
        if match:
            return bool(data['result']), str(match.group(1))
