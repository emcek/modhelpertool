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


# @mark.parametrize('online_tag, result', [('1.1.1', (True, version.parse('1.1.1'), 'github.com/fake.tgz', '09 August 2021', 'Pre-release', 'fake.tgz')),
#                                          ('3.2.1', (False, version.parse('3.2.1'), 'github.com/fake.tgz', '09 August 2021', 'Pre-release', 'fake.tgz'))])
# def test_check_ver_is_possible(online_tag, result):
#     with patch.object(.utils, 'Popen') as response_get:
#         type(response_get.return_value).ok = PropertyMock(return_value=True)
#         type(response_get.return_value).json = MagicMock(return_value={'tag_name': online_tag, 'prerelease': True,
#                                                                        'assets': [{'browser_download_url': 'github.com/fake.tgz'}],
#                                                                        'published_at': '2021-08-09T16:41:51Z'})
#         assert utils.check_ver_at_github(repo='fake1/package1', current_ver='1.1.1') == result