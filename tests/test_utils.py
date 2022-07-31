from unittest.mock import patch

from pytest import mark

from moht import utils


def test_parse_cleaning_success():
    err = ""
    out = """CLEANING: "FLG - Balmora's Underworld V1.1.esp" ...
Loaded cached Master: <DATADIR>/morrowind.esm
Loaded cached Master: <DATADIR>/tribunal.esm
Loaded cached Master: <DATADIR>/bloodmoon.esm
 Cleaned duplicate record (STAT): in_dwrv_corr3_02
 Cleaned redundant AMBI,WHGT from CELL: omaren ancestral tomb
Output saved in: "1/FLG - Balmora's Underworld V1.1.esp"
Original unaltered: "FLG - Balmora's Underworld V1.1.esp"

Cleaning Stats for "FLG - Balmora's Underworld V1.1.esp":
                duplicate record:     1
             redundant CELL.AMBI:     1
             redundant CELL.WHGT:     1"""
    assert utils.parse_cleaning(out, err, "FLG - Balmora's Underworld V1.1.esp") == (True, 'saved')


def test_parse_cleaning_not_modified():
    err = ""
    out = """CLEANING: "FLG - Balmora's Underworld V1.1.esp" ...
Loaded cached Master: <DATADIR>/morrowind.esm
Loaded cached Master: <DATADIR>/tribunal.esm
Loaded cached Master: <DATADIR>/bloodmoon.esm
FLG - Balmora's Underworld V1.1.esp was not modified"""
    assert utils.parse_cleaning(out, err, "FLG - Balmora's Underworld V1.1.esp") == (False, 'not modified')


def test_parse_cleaning_no_master():
    err = """Use of uninitialized value in -s at /home/emc/git/Modding-OpenMW/modhelpertool/moht/tes3cmd-0.37w line 6282.
Use of uninitialized value $curr_size in numeric eq (==) at /home/emc/git/Modding-OpenMW/modhelpertool/moht/tes3cmd-0.37w line 6283.
Use of uninitialized value $curr_size in concatenation (.) or string at /home/emc/git/Modding-OpenMW/modhelpertool/moht/tes3cmd-0.37w line 6287.
Cache Invalidated for: oaab_data.esm (curr_size == , prev_size == 1269934) at /home/emc/git/Modding-OpenMW/modhelpertool/moht/tes3cmd-0.37w line 6287.

[ERROR (Caldera.esp): Master: oaab_data.esm not found in <DATADIR>]"""
    out = """CLEANING: "Caldera.esp" ...
Loaded cached Master: <DATADIR>/morrowind.esm
Loaded cached Master: <DATADIR>/tribunal.esm
Loaded cached Master: <DATADIR>/bloodmoon.esm
Loading Master: oaab_data.esm
Caldera.esp was not modified"""
    assert utils.parse_cleaning(out, err, 'Caldera.esp') == (False, 'oaab_data.esm not found')


def test_parse_cleaning_check_bin_no_config_inifiles():
    err = """Can't locate Config/IniFiles.pm in @INC (you may need to install the Config::IniFiles module) (@INC contains: /usr/lib/perl5/5.36/site_perl /usr/share/perl5/site_perl /usr/lib/perl5/5.36/vendor_perl /usr/share/perl5/vendor_perl /usr/lib/perl5/5.36/core_perl /usr/share/perl5/core_perl) at /home/emc/git/Modding-OpenMW/modhelpertool/moht/tes3cmd-0.37w line 107.
BEGIN failed--compilation aborted at /home/emc/git/Modding-OpenMW/modhelpertool/moht/tes3cmd-0.37w line 107."""
    out = ""
    assert utils.parse_cleaning(out, err, 'Caldera.esp') == (False, 'Config::IniFiles module')


def test_parse_cleaning_check_bin_ok():
    err = """WARNING: Can't find "Data Files" directory, functionality reduced. You should first cd (change directory) to somewhere under where Morrowind is installed.
Usage: tes3cmd COMMAND OPTIONS plugin...
VERSION: 0.37w
tes3cmd is a low-level command line tool that can examine, edit, and delete
records from a TES3 plugin for Morrowind. It can also generate various patches
and clean plugins too.
COMMANDS
  active
    Add/Remove/List Plugins in your load order.
  clean
    Clean plugins of Evil GMSTs, junk cells, and more.
  common
    Find record IDs common between two plugins."""
    out = ""
    assert utils.parse_cleaning(out, err, 'Caldera.esp') == (True, 'Usage')


def test_run_cmd():
    from sys import platform
    from os import path, sep
    tes3cmd = 'tes3cmd-0.37v.exe' if platform == 'win32' else 'tes3cmd-0.37w'
    here = path.abspath(path.dirname(__file__))
    up = f'..{sep}moht{sep}'
    plugin = 'some_plugin.esp'
    cmd = f'{path.join(here, up, tes3cmd)} clean {plugin}'
    out, err = utils.run_cmd(cmd)
    cleaning = utils.parse_cleaning(out, err, plugin)
    if not cleaning:
        assert cleaning is None
        assert out == f'\nCLEANING: "{plugin}" ...\n'
        assert f'FATAL ERROR ({plugin}): Invalid input file (No such file or directory)' in err
    else:
        assert cleaning  == (False, 'Config::IniFiles module')


@mark.parametrize('local_ver, out_err, result', [
    ('0.37.0', ("""Collecting tox==3.25.1
  Using cached tox-3.25.1-py2.py3-none-any.whl (85 kB)
Collecting wheel==0.37.1
  Using cached wheel-0.37.1-py2.py3-none-any.whl (35 kB)
Requirement already satisfied: pluggy>=0.12.0 in /home/emc/.pyenv/versions/3.10.5/envs/moth310/lib/python3.10/site-packages (from tox==3.25.1) (1.0.0)
Would install tox-3.25.1 wheel-0.37.1""", ""), (False, '0.37.1')),
    ('0.37.1', ("Requirement already satisfied: wheel==0.37.1 in /home/emc/.pyenv/versions/3.10.5/envs/moth310/lib/python3.10/site-packages (0.37.1)", ""), (True, '0.37.1')),
    ('0.37.1', ("", """Usage:   
  pip install [options] <requirement specifier> [package-index-options] ...
  pip install [options] -r <requirements file> [package-index-options] ...
  pip install [options] [-e] <vcs project url> ...
  pip install [options] [-e] <local project path> ...
  pip install [options] <archive url/path> ...

no such option: --dry-run
"""), (True, '--dry-run')),
])
def test_is_latest_ver(local_ver, out_err, result):
    with patch.object(utils, 'run_cmd') as run_cmd_mock:
        run_cmd_mock.return_value = out_err
        assert utils.is_latest_ver('wheel', current_ver=local_ver) == result
