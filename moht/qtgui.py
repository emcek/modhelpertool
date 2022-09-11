import traceback
import webbrowser
from argparse import Namespace
from functools import partial
from logging import getLogger
from os import path, chdir, remove
from pathlib import Path
from pprint import pformat
from shutil import move, copy2
from sys import exc_info, version_info, platform
from tempfile import gettempdir
from time import time
from typing import Optional, Callable, Dict, Tuple, Union, List

import qtawesome
from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QDialog, QFileDialog, QTreeWidgetItem, QApplication, QStatusBar,
    QProgressBar, QStackedWidget, QTreeWidget, QAction, QPushButton, QCheckBox, QLineEdit, QLabel, QRadioButton
)

from moht import VERSION, TES3CMD, utils, qtgui_rc
from moht.utils import write_config, read_config

_ = qtgui_rc  # prevent to remove import statement accidentally
REP_COL_PLUGIN = 0
REP_COL_STATUS = 1
REP_COL_TIME = 2


def tr(text: str, context='@default'):
    """
    Translate wrapper function.

    :param text: string to translate
    :param context: for translation
    :return:
    """
    return QtCore.QCoreApplication.translate(context=context, sourceText=text)


def load_ui(ui_path: str, parent: QtWidgets) -> None:
    """
    Load ui file from resources.

    :param ui_path: resources path to ui file
    :param parent: QtWidgets instance
    """
    ui_file = QtCore.QFile(ui_path)
    ui_file.open(QtCore.QIODevice.ReadOnly)
    try:
        uic.loadUi(ui_file, parent)
    finally:
        ui_file.close()


class MohtQtGui(QMainWindow):
    def __init__(self, cli_args: Namespace) -> None:
        """
        Mod Helper Tool Qt5 GUI.

        :param cli_args: Parameters from CLI
        """
        super().__init__()
        self._find_children()
        self.logger = getLogger(__name__)
        load_ui(':/ui/ui/qtgui.ui', self)
        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.logger.debug(f'QThreadPool with {self.threadpool.maxThreadCount()} thread(s)')
        self._le_status = {'le_mods_dir': False, 'le_morrowind_dir': False, 'le_tes3cmd': False}
        self.auto_save = False
        self.progress = 0
        self.no_of_plugins = 0
        self.missing_esm: List[Path] = []
        self.duration = 0.0
        self.conf_file = ''
        self.config = {}
        self._cfg_dir_last = ''
        self._mods_dir_last = ''
        self._morrowind_dir_last = ''
        self._tes3cmd_last = ''
        self._init_menu_bar()
        self._init_radio_buttons()
        self._init_check_boxes()
        self._init_line_edits()
        self._init_tree_report()
        yamlfile = path.join(utils.here(__file__), 'default.yaml')
        if cli_args.yamlfile:
            yamlfile = cli_args.yamlfile
        self._apply_gui_configuration(yamlfile)
        # need read configuration first
        self._init_buttons()
        self.statusbar.showMessage(self.tr('ver. {0}').format(VERSION))
        self._set_icons()

    def _init_menu_bar(self) -> None:
        self.actionLoad.triggered.connect(self.load_config)
        self.actionSave.triggered.connect(self.save_config)
        self.actionSave_as.triggered.connect(self.save_config_as)
        self.actionQuit.triggered.connect(self.close)
        self.actionAboutMoht.triggered.connect(AboutDialog(self).open)
        self.actionAboutQt.triggered.connect(partial(self._show_message_box, kind_of='aboutQt', title='About Qt'))
        self.actionReportIssue.triggered.connect(self._report_issue)
        self.actionCheckUpdates.triggered.connect(self._check_updates)

    def _init_buttons(self) -> None:
        self.pb_mods_dir.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=True,
                                                 last_dir=lambda: self._mods_dir_last, widget_name='le_mods_dir'))
        self.pb_morrowind_dir.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=True,
                                                      last_dir=lambda: self._morrowind_dir_last, widget_name='le_morrowind_dir'))
        self.pb_tes3cmd.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=False,
                                                last_dir=lambda: self._tes3cmd_last, widget_name='le_tes3cmd'))
        self.pb_clean.clicked.connect(self._pb_clean_clicked)
        self.pb_chk_updates.clicked.connect(self._check_updates)
        self.pb_report.clicked.connect(partial(self.stacked_clean.setCurrentIndex, 1))
        self.pb_back_clean.clicked.connect(partial(self.stacked_clean.setCurrentIndex, 0))
        self.pb_load.clicked.connect(self.load_config)
        self.pb_save.clicked.connect(self.save_config)

    def _init_line_edits(self):
        self.le_mods_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='mods_dir'))
        self.le_morrowind_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='morrowind_dir'))
        self.le_tes3cmd.textChanged.connect(partial(self._is_file_exists, widget_name='tes3cmd'))
        self.le_mods_dir.textChanged.connect(self.trigger_autosave)
        self.le_morrowind_dir.textChanged.connect(self.trigger_autosave)
        self.le_tes3cmd.textChanged.connect(self.trigger_autosave)

    def _init_radio_buttons(self):
        self.rb_custom.toggled.connect(self._rb_custom_toggled)
        for ver in [37, 40]:
            getattr(self, f'rb_{ver}').toggled.connect(partial(self._rb_tes3cmd_toggled, ver))

    def _init_check_boxes(self):
        self.cb_auto_save.toggled.connect(self.autosave_toggled)
        self.cb_rm_backup.toggled.connect(self.trigger_autosave)
        self.cb_rm_cache.toggled.connect(self.trigger_autosave)

    def _init_tree_report(self):
        self.tree_report.setColumnWidth(REP_COL_PLUGIN, 400)
        self.tree_report.setColumnWidth(REP_COL_STATUS, 140)
        self.tree_report.setColumnWidth(REP_COL_TIME, 60)
        self.tree_report.itemDoubleClicked.connect(self._item_double_clicked)

    def _clear_tree_report(self):
        self.tree_report.clear()
        self.top_cleaned = QTreeWidgetItem([self.tr('Cleaned: 0'), '', '', ''])
        self.top_error = QTreeWidgetItem([self.tr('Error: 0'), '', '', ''])
        self.top_clean = QTreeWidgetItem([self.tr('Clean: 0'), '', '', ''])
        self.tree_report.addTopLevelItem(self.top_cleaned)
        self.tree_report.addTopLevelItem(self.top_error)
        self.tree_report.addTopLevelItem(self.top_clean)
        self.tree_report.itemDoubleClicked.connect(self._item_double_clicked)
        header = self.tree_report.headerItem()
        header.setToolTip(REP_COL_PLUGIN, self.tr('Double click on item to copy plugin`s path.'))
        header.setToolTip(REP_COL_TIME, self.tr('Cleaning time in min:sec\nHold on item to see cleaning details.'))

    def _rb_tes3cmd_toggled(self, version: int, state: bool) -> None:
        if state:
            self._set_le_tes3cmd(TES3CMD[platform][version])
        self.trigger_autosave()

    def _rb_custom_toggled(self, state: bool) -> None:
        self.le_tes3cmd.setEnabled(state)
        self.pb_tes3cmd.setEnabled(state)
        self.trigger_autosave()

    def _pb_clean_clicked(self) -> None:
        self.progressbar.setValue(0)
        self.progress = 0
        self._clear_tree_report()
        self.pb_report.setEnabled(True)
        self._set_icons(button='pb_clean', icon_name='fa5s.spinner', color='green', spin=True)
        self.pb_clean.disconnect()
        all_plugins = utils.get_all_plugins(mods_dir=self.mods_dir)
        self.logger.debug(f'all_plugins: {len(all_plugins)}:\n{pformat(all_plugins)}')
        if self.cb_clean_all.isChecked():
            plugins_to_clean = all_plugins
        else:
            plugins_to_clean = utils.get_plugins_to_clean(plugins=all_plugins)
        self.no_of_plugins = len(plugins_to_clean)
        self.logger.debug(f'to_clean: {self.no_of_plugins}:\n{pformat(plugins_to_clean)}')
        self.statusbar.showMessage(self.tr('Plugins to clean: {0} - See Report').format(self.no_of_plugins))
        req_esm = utils.get_required_esm(plugins=plugins_to_clean)
        self.logger.debug(f'Required esm: {req_esm}')
        self.missing_esm = utils.find_missing_esm(dir_path=self.mods_dir, data_files=self.morrowind_dir, esm_files=req_esm)
        utils.copy_filelist(self.missing_esm, self.morrowind_dir)
        self.duration = time()
        self.progressbar.setValue(int(100 / (self.no_of_plugins * 2)))
        for idx, plug in enumerate(plugins_to_clean, 1):
            self.logger.debug(f'Start: {idx} / {self.no_of_plugins}')
            self.run_in_background(job=partial(self._clean_start, plug=plug),
                                   signal_handlers={'error': self._error_during_clean,
                                                    'result': self._clean_finished})

    def _clean_start(self, plug: Path) -> Tuple[Path, bool, str, float, str, str]:
        start = time()
        chdir(self.morrowind_dir)
        self.logger.debug(f'Copy: {plug} -> {self.morrowind_dir}')
        copy2(plug, self.morrowind_dir)
        mod_file = utils.extract_filename(plug)
        out, err = utils.run_cmd(f'{self.tes3cmd} clean --output-dir --overwrite "{mod_file}"')
        result, reason = utils.parse_cleaning(out, err, mod_file)
        self.logger.debug(f'Result: {result}, Reason: {reason}')
        if result:
            clean_plugin = path.join(self.morrowind_dir, '1', mod_file)
            self.logger.debug(f'Move: {clean_plugin} -> {plug}')
            move(clean_plugin, plug)
        if self.cb_rm_backup.isChecked():
            mod_path = path.join(self.morrowind_dir, mod_file)
            self.logger.debug(f'Remove: {mod_path}')
            remove(mod_path)
        self.logger.debug(f'Done: {mod_file}')
        duration = time() - start
        return plug, result, reason, duration, out, err

    def _error_during_clean(self, exc_tuple: Tuple[Exception, str, str]) -> None:
        exc_type, exc_val, exc_tb = exc_tuple
        self.logger.warning(f'{exc_type.__class__.__name__}: {exc_val}')
        self.logger.debug(exc_tb)

    def _clean_finished(self, clean_result: Tuple[Path, bool, str, float, str, str]) -> None:
        self._add_report_data(*clean_result)
        self.progress += 1
        percent = self.progress * 100 / self.no_of_plugins
        self.logger.debug(f'Progress: {percent:.2f} %')
        self.progressbar.setValue(int(percent))
        if self.progress == self.no_of_plugins:
            self._clean_done()

    def _clean_done(self) -> None:
        self.progressbar.setValue(100)
        if self.cb_rm_cache.isChecked():
            cachedir = 'tes3cmd' if platform == 'win32' else '.tes3cmd-3'
            utils.rm_dirs_with_subdirs(dir_path=self.morrowind_dir, subdirs=['1', cachedir])
        utils.rm_copied_extra_esm(self.missing_esm, self.morrowind_dir)
        cleaning_time = time() - self.duration
        self.logger.debug(f'Total time: {cleaning_time} s')
        self._set_icons(button='pb_clean', icon_name='fa5s.hand-sparkles', color='brown')
        if cleaning_time <= 60.0:
            duration = f'{utils.get_string_duration(seconds=cleaning_time, time_format="%S")} [sec]'
        else:
            duration = f'{utils.get_string_duration(seconds=cleaning_time, time_format="%M:%S")} [min:sec]'
        self.statusbar.showMessage(self.tr('Done. Took: {0}').format(duration))
        self.pb_clean.clicked.connect(self._pb_clean_clicked)

    def _add_report_data(self, plug: Path, result: bool, reason: str, cleaning_time: float, out: str, err: str):
        error_txt = '\n'.join(reason.split('**'))
        if 'not found' in reason:
            reason = 'missing esm'
        mod_file = utils.extract_filename(plug)
        item = QTreeWidgetItem([mod_file, reason, f'{utils.get_string_duration(cleaning_time)}'])
        item.setToolTip(REP_COL_PLUGIN, f'{plug}')
        item.setToolTip(REP_COL_TIME, f'{out.strip()}\n{err.strip()}')
        if result:
            self._report_icon_update_plugin_number(top_item=self.top_cleaned, child_item=item, icon=qtawesome.icon('fa5s.check', color='green'))
        elif not result and reason == 'not modified':
            self._report_icon_update_plugin_number(top_item=self.top_clean, child_item=item, icon=qtawesome.icon('fa5s.check', color='green'))
        elif not result and 'missing esm' in reason:
            self._report_icon_update_plugin_number(top_item=self.top_error, child_item=item, icon=qtawesome.icon('fa5s.times', color='red'), tip_text=error_txt)

    def _report_icon_update_plugin_number(self, top_item: QTreeWidgetItem, child_item: QTreeWidgetItem, icon: QIcon, tip_text: str = ''):
        child_item.setIcon(REP_COL_STATUS, icon)
        if tip_text:
            child_item.setToolTip(REP_COL_STATUS, tip_text)
        top_item.addChild(child_item)
        top_text = top_item.text(REP_COL_PLUGIN).split(' ')
        top_item.setText(REP_COL_PLUGIN, f'{top_text[0]} {int(top_text[1]) + 1}')
        self.tree_report.expandItem(top_item)

    def _item_double_clicked(self, item: QTreeWidgetItem) -> None:
        """
        Copy tool tip text of first column of clicked tree item to clipboard.

        :param item: item clicked
        """
        if item.parent():
            QApplication.clipboard().setText(item.toolTip(REP_COL_PLUGIN))
            self.statusbar.showMessage(self.tr('Path of plugin copied to clipboard'))

    def _check_updates(self):
        _, desc = utils.is_latest_ver(package='moht', current_ver=VERSION)
        self.statusbar.showMessage(self.tr('ver. {0} - {1}').format(VERSION, desc))

    def _set_le_tes3cmd(self, tes3cmd: str) -> None:
        self.tes3cmd = path.join(utils.here(__file__), 'resources', tes3cmd)

    def _is_dir_exists(self, text: str, widget_name: str) -> None:
        dir_exists = path.isdir(text)
        self.logger.debug(f'Path: {text} for le_{widget_name} exists: {dir_exists}')
        self._line_edit_handling_and_last_directory(widget_name, dir_exists, text)

    def _is_file_exists(self, text: str, widget_name) -> None:
        file_exists = path.isfile(text)
        self.logger.debug(f'Path: {text} for le_{widget_name} exists: {file_exists}')
        self._line_edit_handling_and_last_directory(widget_name, file_exists, text)

    def _line_edit_handling_and_last_directory(self, widget_name: str, path_exists: bool, path_name: str) -> None:
        """
        Mark text of LineEdit as red if path does not exist.

        Save last visited path (starting directory for QFileWidget) base of path_name.

        :param widget_name: widget name
        :param path_exists: bool for path existence
        :param path_name: full path name
        """
        self._le_status[f'le_{widget_name}'] = path_exists
        if path_exists and widget_name == 'tes3cmd':
            getattr(self, f'le_{widget_name}').setStyleSheet('')
            setattr(self, f'_{widget_name}_last', utils.parent_dir(path_name))
            result = self._check_clean_bin()
            if not result:
                self._le_status[f'le_{widget_name}'] = result
                getattr(self, f'le_{widget_name}').setStyleSheet('color: red;')
        elif path_exists and widget_name != 'tes3cmd':
            getattr(self, f'le_{widget_name}').setStyleSheet('')
            setattr(self, f'_{widget_name}_last', utils.parent_dir(path_name))
        else:
            getattr(self, f'le_{widget_name}').setStyleSheet('color: red;')
        self._handle_clean_button()

    def _handle_clean_button(self) -> None:
        """Enable /disable Clean button base on status of LineEdits."""
        if all(self._le_status.values()):
            self.pb_clean.setEnabled(True)
        else:
            self.pb_clean.setEnabled(False)

    def _check_clean_bin(self) -> bool:
        self.logger.debug('Checking tes3cmd')
        try:
            out, err = utils.run_cmd(f'{self.tes3cmd} help')
            result, reason = utils.parse_cleaning(out, err, '')
        except OSError as exp:
            self.logger.debug('Checking selected tes3cmd file', exc_info=True)
            result = False
            reason = str(exp)
        self.logger.debug(f'Result: {result}, Reason: {reason}')
        if not result:
            self.statusbar.showMessage(self.tr('Error: {0}').format(reason))
            if 'Config::IniFiles' in reason:
                msg = self.tr('''
Check for `perl-Config-IniFiles` or a similar package.
Use you package manage:

Arch / Manjaro (AUR):
yay -S perl-config-inifiles

Gentoo:
emerge dev-perl/Config-IniFiles

Debian / Ubuntu / Mint:
apt install libconfig-inifiles-perl

OpenSUSE:
zypper install perl-Config-IniFiles

Fedora / CentOS / RHEL:
dnf install perl-Config-IniFiles.noarch''')
            elif 'Not tes3cmd' in reason:
                msg = self.tr('Selected file is not a valid tes3cmd executable.\n\nPlease select a correct binary file.')
            else:
                msg = reason
            self._show_message_box(kind_of='warning', title='Not tes3cmd', message=msg)
        return result

    # <=><=><=><=><=><=><=><=><=><=><=> configuration <=><=><=><=><=><=><=><=><=><=><=>
    def load_config(self) -> None:
        """Load GUI configuration."""
        self.statusbar.showMessage('Choose configuration file')
        self._cfg_dir_last = self._cfg_dir_last if self._cfg_dir_last else str(Path.home())
        conf_file = self._run_file_dialog(for_load=True, for_dir=False,
                                          last_dir=lambda: self._cfg_dir_last, file_filter='Yaml Files [*.yaml *.yml](*.yaml *.yml)')
        self._cfg_dir_last = utils.parent_dir(conf_file)
        if conf_file:
            self.conf_file = conf_file
            self._apply_gui_configuration(yamlfile=self.conf_file)
            self.statusbar.showMessage(f'Configuration loaded: {self.conf_file}')

    def save_config(self) -> None:
        """Save GUI configuration."""
        if not self.conf_file:
            self.statusbar.showMessage('Choose configuration file')
            self._cfg_dir_last = self._cfg_dir_last if self._cfg_dir_last else str(Path.home())
            self.conf_file = self._run_file_dialog(for_load=False, for_dir=False,
                                                   last_dir=lambda: self._cfg_dir_last, file_filter='Yaml Files [*.yaml *.yml](*.yaml *.yml)')
            self._cfg_dir_last = utils.parent_dir(self.conf_file)
        try:
            self.config = self._dump_gui_configuration()
            write_config(self.config, self.conf_file)
            self.statusbar.showMessage(f'Configuration saved: {self.conf_file}')
        except IOError:
            self.cb_auto_save.setChecked(False)
            self.statusbar.showMessage('Configuration not saved')

    def save_config_as(self) -> None:
        """Save as GUI configuration."""
        self.conf_file = ''
        self.save_config()

    def _apply_gui_configuration(self, yamlfile: str) -> bool:
        """
        Apply configuration from internal dict to GUI widgets.

        :param yamlfile: absolute path to configuration yaml
        :return: True if success
        """
        self.config = read_config(yamlfile)
        if self.config.get('moht', {}).get('auto_save', False):
            self.cb_auto_save.toggled.disconnect()
            self.auto_save = True
            self.config['moht']['auto_save'] = False
        for cfg_section in self.config:
            getattr(self, '_apply_cfg_{}'.format(cfg_section))(self.config[cfg_section])
        if self.auto_save:
            self.config['moht']['auto_save'] = True
            self.cb_auto_save.setChecked(True)
            self.cb_auto_save.toggled.connect(self.autosave_toggled)
        return True

    def _apply_cfg_moht(self, cfg_dict: Dict[str, Union[str, int, bool]]) -> None:
        self.logger.debug(f'Apply configuration for API ver: {cfg_dict["api_ver"]}')
        self.cb_auto_save.setChecked(cfg_dict['auto_save'])

    def _apply_cfg_tes3cmd_clean(self, cfg_dict: Dict[str, Union[str, int, bool]]) -> None:
        mod_dir = cfg_dict['mod_dir']
        data_files = cfg_dict['data_files_dir']
        tes3bin = cfg_dict['tes3cmd_bin']
        tes_ver = cfg_dict['tes3cmd_ver']
        self.mods_dir = mod_dir if mod_dir else str(Path.home())
        self.morrowind_dir = data_files if data_files else str(Path.home())
        self.tes3cmd = tes3bin if tes3bin else path.join(utils.here(__file__), 'resources', TES3CMD[platform][tes_ver])
        self.tes3cmd_ver = tes_ver
        self.cb_rm_backup.setChecked(cfg_dict['clean_backup'])
        self.cb_rm_cache.setChecked(cfg_dict['clean_cache'])
        self.cb_clean_all.setChecked(cfg_dict['clean_all'])

    def _dump_gui_configuration(self) -> Dict[str, Dict[str, Union[str, int, bool]]]:
        """
        Dump GUI configuration to python dict.

        :return: GUI configuration as dict
        """
        c = {
            'moht': {
                'api_ver': VERSION,
                'auto_save': self.cb_auto_save.isChecked()
            },
            'tes3cmd_clean': {
                'mod_dir': self.mods_dir,
                'data_files_dir': self.morrowind_dir,
                'tes3cmd_bin': self.tes3cmd,
                'tes3cmd_ver': self.tes3cmd_ver,
                'clean_backup': self.cb_rm_backup.isChecked(),
                'clean_cache': self.cb_rm_cache.isChecked(),
                'clean_all': self.cb_clean_all.isChecked(),
            },
        }
        return c

    def autosave_toggled(self) -> None:
        """Action for autosave checkbox toggle."""
        if self.cb_auto_save.isChecked():
            self.save_config()
        else:
            self.conf_file = ''
            self.statusbar.clearMessage()

    # <=><=><=><=><=><=><=><=><=><=><=> helpers <=><=><=><=><=><=><=><=><=><=><=>
    def trigger_autosave(self) -> None:
        """Just trigger save configuration if auto save checkbox is checked."""
        if self.cb_auto_save.isChecked():
            self.save_config()

    def run_in_background(self, job: Union[partial, Callable], signal_handlers: Dict[str, Callable]) -> None:
        """
        Setup worker with signals callback to schedule GUI job in background.

        signal_handlers parameter is a dict with signals from  WorkerSignals,
        possibles signals are: finished, error, result, progress. Values in dict
        are methods/callables as handlers/callbacks for particular signal.

        :param job: GUI method or function to run in background
        :param signal_handlers: signals as keys: finished, error, result, progress and values as callable
        """
        progress = True if 'progress' in signal_handlers.keys() else False
        worker = Worker(func=job, with_progress=progress)
        for signal, handler in signal_handlers.items():
            getattr(worker.signals, signal).connect(handler)
        if isinstance(job, partial):
            job_name = job.func.__name__
            args = job.args
            kwargs = job.keywords
        else:
            job_name = job.__name__
            args = tuple()
            kwargs = dict()
        signals = {signal: handler.__name__ for signal, handler in signal_handlers.items()}
        self.logger.debug(f'bg job for: {job_name} args: {args} kwargs: {kwargs} signals {signals}')
        self.threadpool.start(worker)

    def _set_icons(self, button: Optional[str] = None, icon_name: Optional[str] = None, color: str = 'black', spin: bool = False):
        """
        Universal method to set icon for QPushButtons.

        When button is provided without icon_name, current button icon will be removed.
        When none of button nor icon_name are provided, default starting icons are set for all buttons.

        :param button: button name
        :param icon_name: ex: spinner, check, times, pause
        :param color: ex: red, green, black
        :param spin: spinning icon: True or False
        """
        if not (button or icon_name):
            self.pb_mods_dir.setIcon(qtawesome.icon('fa5s.folder', color='brown'))
            self.pb_morrowind_dir.setIcon(qtawesome.icon('fa5s.folder', color='brown'))
            self.pb_tes3cmd.setIcon(qtawesome.icon('fa5s.file', color='brown'))
            self.pb_clean.setIcon(qtawesome.icon('fa5s.hand-sparkles', color='brown'))
            self.pb_report.setIcon(qtawesome.icon('fa5s.file-contract', color='brown'))
            self.pb_back_clean.setIcon(qtawesome.icon('fa5s.arrow-left', color='brown'))
            self.pb_chk_updates.setIcon(qtawesome.icon('fa5s.arrow-down', color='brown'))
            self.pb_close.setIcon(qtawesome.icon('fa5s.sign-out-alt', color='brown'))
            return
        btn = getattr(self, button)  # type: ignore
        if spin and icon_name:
            icon = qtawesome.icon(f'{icon_name}', color=color, animation=qtawesome.Spin(btn, 2, 1))
        elif not spin and icon_name:
            icon = qtawesome.icon(f'{icon_name}', color=color)
        else:
            icon = QIcon()
        btn.setIcon(icon)

    def _run_file_dialog(self, for_load: bool, for_dir: bool, last_dir: Callable[..., str],
                         widget_name: Optional[str] = None, file_filter: str = 'All Files [*.*](*.*)') -> str:
        """
        Handling open/save dialog to select file or folder.

        :param for_load: if True show window for load, for save otherwise
        :param for_dir: if True show window for selecting directory only, if False selecting file only
        :param last_dir: function return last selected dir
        :param widget_name: update text for widget
        :param file_filter: list of types of files ;;-seperated: Text [*.txt](*.txt)
        :return: full path to file or directory
        """
        result_path = ''
        if file_filter != 'All Files [*.*](*.*)':
            file_filter = f'{file_filter};;All Files [*.*](*.*)'
        if for_load and for_dir:
            result_path = QFileDialog.getExistingDirectory(self, caption='Open Directory', directory=last_dir(),
                                                           options=QFileDialog.Option.ShowDirsOnly)
        if for_load and not for_dir:
            result_path = QFileDialog.getOpenFileName(self, caption='Open File', directory=last_dir(),
                                                      filter=file_filter, options=QFileDialog.Option.ReadOnly)[0]
        if not for_load and not for_dir:
            result_path = QFileDialog.getSaveFileName(self, caption='Save File', directory=last_dir(),
                                                      filter=file_filter, options=QFileDialog.Option.ReadOnly)[0]
        if widget_name is not None and result_path:
            getattr(self, widget_name).setText(result_path)
        return result_path

    def _show_message_box(self, kind_of: str, title: str, message: str = '') -> None:
        """
        Generic method to show any QMessageBox delivered with Qt.

        :param kind_of: any of: information, question, warning, critical, about or aboutQt
        :param title: Title of modal window
        :param message: text of message, default is empty
        """
        message_box = getattr(QMessageBox, kind_of)
        if kind_of == 'aboutQt':
            message_box(self, title)
        else:
            message_box(self, title, message)

    @staticmethod
    def _report_issue():
        webbrowser.open('https://gitlab.com/modding-openmw/modhelpertool/issues', new=2)

    @property
    def mods_dir(self) -> str:
        """
        Get root of mods directory.

        :return: mods dir as string
        """
        return self.le_mods_dir.text()

    @mods_dir.setter
    def mods_dir(self, value: str) -> None:
        self.le_mods_dir.setText(value)

    @property
    def morrowind_dir(self) -> str:
        """
        Get Morrowind Data Files directory.

        :return: morrowind dir as string
        """
        return self.le_morrowind_dir.text()

    @morrowind_dir.setter
    def morrowind_dir(self, value: str) -> None:
        self.le_morrowind_dir.setText(value)

    @property
    def tes3cmd(self) -> str:
        """
        Get tes3cmd binary file path.

        :return: tes3cmd file as string
        """
        return self.le_tes3cmd.text()

    @tes3cmd.setter
    def tes3cmd(self, value: str) -> None:
        self.le_tes3cmd.setText(value)

    @property
    def tes3cmd_ver(self) -> str:
        """
        Get tes3cmd version RadioButton.

        :return: tes3cmd version as string
        """
        for ver in [37, 40, 'custom']:
            rb = getattr(self, f'rb_{ver}')
            if rb.isChecked():
                return ver

    @tes3cmd_ver.setter
    def tes3cmd_ver(self, value: str) -> None:
        try:
            getattr(self, f'rb_{value}').setChecked(True)
        except AttributeError:
            self.logger.debug(f'Can not change select: rb_{value}')

    def _find_children(self) -> None:
        self.actionLoad = self.findChild(QAction, 'actionLoad')
        self.actionSave = self.findChild(QAction, 'actionSave')
        self.actionSave_as = self.findChild(QAction, 'actionSave_as')
        self.actionQuit = self.findChild(QAction, 'actionQuit')
        self.actionAboutMoht = self.findChild(QAction, 'actionAboutMoht')
        self.actionAboutQt = self.findChild(QAction, 'actionAboutQt')
        self.actionReportIssue = self.findChild(QAction, 'actionReportIssue')
        self.actionCheckUpdates = self.findChild(QAction, 'actionCheckUpdates')

        self.pb_mods_dir = self.findChild(QPushButton, 'pb_mods_dir')
        self.pb_morrowind_dir = self.findChild(QPushButton, 'pb_morrowind_dir')
        self.pb_tes3cmd = self.findChild(QPushButton, 'pb_tes3cmd')
        self.pb_report = self.findChild(QPushButton, 'pb_report')
        self.pb_back_clean = self.findChild(QPushButton, 'pb_back_clean')
        self.pb_clean = self.findChild(QPushButton, 'pb_clean')
        self.pb_chk_updates = self.findChild(QPushButton, 'pb_chk_updates')
        self.pb_close = self.findChild(QPushButton, 'pb_close')
        self.pb_load = self.findChild(QPushButton, 'pb_load')
        self.pb_save = self.findChild(QPushButton, 'pb_save')

        self.cb_rm_backup = self.findChild(QCheckBox, 'cb_rm_backup')
        self.cb_rm_cache = self.findChild(QCheckBox, 'cb_rm_cache')
        self.cb_auto_save = self.findChild(QCheckBox, 'cb_auto_save')
        self.cb_clean_all = self.findChild(QCheckBox, 'cb_clean_all')

        self.le_mods_dir = self.findChild(QLineEdit, 'le_mods_dir')
        self.le_morrowind_dir = self.findChild(QLineEdit, 'le_morrowind_dir')
        self.le_tes3cmd = self.findChild(QLineEdit, 'le_tes3cmd')

        self.rb_custom = self.findChild(QRadioButton, 'rb_custom')
        self.statusbar = self.findChild(QStatusBar, 'statusbar')
        self.progressbar = self.findChild(QProgressBar, 'progressbar')
        self.stacked_clean = self.findChild(QStackedWidget, 'stacked_clean')
        self.tree_report = self.findChild(QTreeWidget, 'tree_report')


class AboutDialog(QDialog):
    def __init__(self, parent) -> None:
        """Moht about dialog window."""
        super().__init__(parent)
        load_ui(':/ui/ui/about.ui', self)
        self.label = self.findChild(QLabel, 'label')
        self.setup_text()

    def setup_text(self) -> None:
        """Prepare text information about Moht application."""
        qt_version = f'{QtCore.PYQT_VERSION_STR} / <b>Qt</b>: {QtCore.QT_VERSION_STR}'
        log_path = path.join(gettempdir(), 'moht.log')
        text = self.label.text().rstrip('</body></html>')
        text += self.tr('<p>Attach log file: {0}<br/><br/>').format(log_path)
        text += f'<b>moht:</b> {VERSION}'
        text += '<br><b>python:</b> {0}.{1}.{2}-{3}.{4}'.format(*version_info)
        text += f'<br><b>PyQt:</b> {qt_version}</p></body></html>'
        self.label.setText(text)


class WorkerSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:
    * finished - no data
    * error - tuple with exctype, value, traceback.format_exc()
    * result - object/any type - data returned from processing
    * progress - float between 0 and 1 as indication of progress
    """

    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(float)


class Worker(QtCore.QRunnable):
    def __init__(self, func: Union[partial, Callable], with_progress: bool) -> None:
        """
        Worker thread.

        Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
        :param func: The function callback to run on worker thread
        """
        super().__init__()
        self.func = func
        self.signals = WorkerSignals()
        self.kwargs = {}
        if with_progress:
            self.kwargs['progress_callback'] = self.signals.progress

    @QtCore.pyqtSlot()
    def run(self):
        """Initialise the runner function with passed args, kwargs."""
        try:
            result = self.func(**self.kwargs)
        except Exception:
            exctype, value = exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
