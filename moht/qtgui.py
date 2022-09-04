import traceback
import webbrowser
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
from PyQt5 import QtCore, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDialog, QFileDialog, QTreeWidgetItem, QApplication

from moht import VERSION, TES3CMD, utils, qtgui_rc

resources = qtgui_rc  # prevent to remove import statement accidentally
REP_COL_PLUGIN = 0
REP_COL_STATUS = 1
REP_COL_TIME = 2
MAIN_CLEAR_TAB = 0
MAIN_REPORT_TAB = 1


def tr(text2translate: str):
    """
    Translate wrapper function.

    :param text2translate: string to translate
    :return:
    """
    # return QtCore.QCoreApplication.translate('mw_gui', text2translate)
    return QtCore.QCoreApplication.translate('@default', text2translate)


class MohtQtGui(QMainWindow):
    def __init__(self) -> None:
        """Mod Helper Tool Qt5 GUI."""
        super().__init__()
        self.logger = getLogger(__name__)
        uic.loadUi(f'{utils.here(__file__)}/ui/qtgui.ui', self)
        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.logger.debug(f'QThreadPool with {self.threadpool.maxThreadCount()} thread(s)')
        self._le_status = {'le_mods_dir': False, 'le_morrowind_dir': False, 'le_tes3cmd': False}
        self.progress = 0
        self.no_of_plugins = 0
        self.missing_esm: List[Path] = []
        self.duration = 0.0
        self._init_menu_bar()
        self._init_buttons()
        self._init_radio_buttons()
        self._init_line_edits()
        self._init_tree_report()
        self.statusbar.showMessage(f'ver. {VERSION}')
        self._set_icons()

    def _init_menu_bar(self) -> None:
        self.actionQuit.triggered.connect(self.close)
        self.actionAboutMoht.triggered.connect(AboutDialog(self).open)
        self.actionAboutQt.triggered.connect(partial(self._show_message_box, kind_of='aboutQt', title='About Qt'))
        self.actionReportIssue.triggered.connect(self._report_issue)
        self.actionCheckUpdates.triggered.connect(self._check_updates)

    def _init_buttons(self) -> None:
        self.pb_mods_dir.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=True, widget_name='le_mods_dir'))
        self.pb_morrowind_dir.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=True, widget_name='le_morrowind_dir'))
        self.pb_tes3cmd.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=False, widget_name='le_tes3cmd'))
        self.pb_clean.clicked.connect(self._pb_clean_clicked)
        self.pb_chk_updates.clicked.connect(self._check_updates)

    def _init_line_edits(self):
        self.le_mods_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='le_mods_dir'))
        self.le_morrowind_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='le_morrowind_dir'))
        self.le_tes3cmd.textChanged.connect(partial(self._is_file_exists, widget_name='le_tes3cmd'))
        self._set_le_tes3cmd(TES3CMD[platform]['0_40'])
        self.mods_dir = str(Path.home())
        self.morrowind_dir = str(Path.home())
        # self.mods_dir = '/home/emc/clean/CitiesTowns/'
        # self.morrowind_dir = '/home/emc/.wine/drive_c/GOG Games/Morrowind/Data Files'

    def _init_radio_buttons(self):
        for ver in ['0_37', '0_40']:
            getattr(self, f'rb_{ver}').toggled.connect(partial(self._rb_tes3cmd_toggled, ver))

    def _init_tree_report(self):
        self.tree_report.setColumnWidth(REP_COL_PLUGIN, 400)
        self.tree_report.setColumnWidth(REP_COL_STATUS, 140)
        self.tree_report.setColumnWidth(REP_COL_TIME, 60)
        self.tree_report.itemDoubleClicked.connect(self._item_double_clicked)
        self.tw_main.setTabEnabled(MAIN_REPORT_TAB, False)

    def _clear_tree_report(self):
        self.tree_report.clear()
        self.top_cleaned = QTreeWidgetItem(['Cleaned: 0', '', '', ''])
        self.top_error = QTreeWidgetItem(['Error: 0', '', '', ''])
        self.top_clean = QTreeWidgetItem(['Clean: 0', '', '', ''])
        self.tree_report.addTopLevelItem(self.top_cleaned)
        self.tree_report.addTopLevelItem(self.top_error)
        self.tree_report.addTopLevelItem(self.top_clean)
        self.tree_report.itemDoubleClicked.connect(self._item_double_clicked)
        header = self.tree_report.headerItem()
        header.setToolTip(REP_COL_PLUGIN, 'Double click on item to copy plugin`s path.')
        header.setToolTip(REP_COL_TIME, 'Cleaning time in min:sec\nHold on item to see cleaning details.')
        self.tw_main.setTabEnabled(MAIN_REPORT_TAB, True)

    def _rb_tes3cmd_toggled(self, version: str, state: bool) -> None:
        if state:
            self._set_le_tes3cmd(TES3CMD[platform][version])

    def _pb_clean_clicked(self) -> None:
        self.pbar_clean.setValue(0)
        self.progress = 0
        self._clear_tree_report()
        self._set_icons(button='pb_clean', icon_name='fa5s.spinner', color='green', spin=True)
        self.pb_clean.disconnect()
        all_plugins = utils.get_all_plugins(mods_dir=self.mods_dir)
        self.logger.debug(f'all_plugins: {len(all_plugins)}:\n{pformat(all_plugins)}')
        plugins_to_clean = utils.get_plugins_to_clean(plugins=all_plugins)
        self.no_of_plugins = len(plugins_to_clean)
        self.logger.debug(f'to_clean: {self.no_of_plugins}:\n{pformat(plugins_to_clean)}')
        self.statusbar.showMessage(f'Plugins to clean: {self.no_of_plugins} - See Report tab')
        req_esm = utils.get_required_esm(plugins=plugins_to_clean)
        self.logger.debug(f'Required esm: {req_esm}')
        self.missing_esm = utils.find_missing_esm(dir_path=self.mods_dir, data_files=self.morrowind_dir, esm_files=req_esm)
        utils.copy_filelist(self.missing_esm, self.morrowind_dir)
        self.duration = time()
        self.pbar_clean.setValue(int(100 / (self.no_of_plugins * 2)))
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
        if self.cb_rm_bakup.isChecked():
            mod_path = path.join(self.morrowind_dir, mod_file)
            self.logger.debug(f'Remove: {mod_path}')
            remove(mod_path)
        self.logger.debug(f'Done: {mod_file}')
        duration = time() - start
        return plug, result, reason, duration, out, err

    def _error_during_clean(self, exc_tuple: Tuple[Exception, str, str]) -> None:
        exc_type, exc_val, exc_tb = exc_tuple
        self.logger.warning('{}: {}'.format(exc_type.__class__.__name__, exc_val))
        self.logger.debug(exc_tb)

    def _clean_finished(self, clean_result: Tuple[Path, bool, str, float, str, str]) -> None:
        self._add_report_data(*clean_result)
        self.progress += 1
        percent = self.progress * 100 / self.no_of_plugins
        self.logger.debug(f'Progress: {percent:.2f} %')
        self.pbar_clean.setValue(int(percent))
        if self.progress == self.no_of_plugins:
            self._clean_done()

    def _clean_done(self) -> None:
        self.pbar_clean.setValue(100)
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
        self.statusbar.showMessage(f'Done. Took: {duration}')
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
            self.statusbar.showMessage('Path of plugin copied to clipboard')

    def _check_updates(self):
        _, desc = utils.is_latest_ver(package='moht', current_ver=VERSION)
        self.statusbar.showMessage(f'ver. {VERSION} - {desc}')

    def _set_le_tes3cmd(self, tes3cmd: str) -> None:
        self.tes3cmd = path.join(utils.here(__file__), 'resources', tes3cmd)

    def _update_stats(self, mod_file: str, plug: Path, reason: str, result: bool) -> None:
        if result:
            clean_plugin = path.join(self.morrowind_dir, '1', mod_file)
            self.logger.debug(f'Move: {clean_plugin} -> {plug}')
            move(clean_plugin, plug)
            self.stats['cleaned'] += 1
        if not result and reason == 'not modified':
            self.stats['clean'] += 1
        if not result and 'not found' in reason:
            for res in reason.split('**'):
                self.stats['error'] += 1
                esm = self.stats.get(res, 0)
                esm += 1
                self.stats.update({res: esm})

    def _is_dir_exists(self, text: str, widget_name: str) -> None:
        dir_exists = path.isdir(text)
        self.logger.debug(f'Path: {text} for {widget_name} exists: {dir_exists}')
        self._line_edit_handling(widget_name, dir_exists)

    def _is_file_exists(self, text: str, widget_name) -> None:
        file_exists = path.isfile(text)
        self.logger.debug(f'Path: {text} for {widget_name} exists: {file_exists}')
        self._line_edit_handling(widget_name, file_exists)

    def _line_edit_handling(self, widget_name: str, path_exists: bool) -> None:
        """
        Mark text of LieEdit as red if path does not exist.

        Additionally, save status and enable /disable Clean button base on it.

        :param widget_name: widget name
        :param path_exists: bool for path existence
        """
        self._le_status[widget_name] = path_exists
        if path_exists and widget_name == 'le_tes3cmd':
            getattr(self, widget_name).setStyleSheet('')
            self._le_status[widget_name] = self._check_clean_bin()
        elif path_exists and widget_name != 'le_tes3cmd':
            getattr(self, widget_name).setStyleSheet('')
        else:
            getattr(self, widget_name).setStyleSheet('color: red;')
        if all(self._le_status.values()):
            self.pb_clean.setEnabled(True)
        else:
            self.pb_clean.setEnabled(False)

    def _check_clean_bin(self) -> bool:
        self.logger.debug('Checking tes3cmd')
        out, err = utils.run_cmd(f'{self.tes3cmd} help')
        result, reason = utils.parse_cleaning(out, err, '')
        self.logger.debug(f'Result: {result}, Reason: {reason}')
        if not result:
            self.statusbar.showMessage(f'Error: {reason}')
            msg = ''
            if 'Config::IniFiles' in reason:
                msg = '''
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
dnf install perl-Config-IniFiles.noarch'''
            elif 'Not tes3cmd' in reason:
                msg = 'Selected file is not a valid tes3cmd executable.\n\nPlease select a correct binary file.'
            self._show_message_box(kind_of='warning', title='Not tes3cmd', message=msg)
        return result

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
            self.pb_chk_updates.setIcon(qtawesome.icon('fa5s.arrow-down', color='brown'))
            self.pb_close.setIcon(qtawesome.icon('fa5s.sign-out-alt', color='brown'))
            return
        btn = getattr(self, button)  # type: ignore
        if spin and icon_name:
            icon = qtawesome.icon('{}'.format(icon_name), color=color, animation=qtawesome.Spin(btn, 2, 1))
        elif not spin and icon_name:
            icon = qtawesome.icon('{}'.format(icon_name), color=color)
        else:
            icon = QIcon()
        btn.setIcon(icon)

    def _run_file_dialog(self, for_load: bool, for_dir: bool, widget_name: Optional[str] = None, file_filter: str = 'All Files [*.*](*.*)') -> str:
        """
        Handling open/save dialog to select file or folder.

        :param for_load: if True show window for load, for save otherwise
        :param for_dir: if True show window for selecting directory only, if False selectting file only
        :param file_filter: list of types of files ;;-seperated: Text [*.txt](*.txt)
        :return: full path to file or directory
        """
        result_path = ''
        if file_filter != 'All Files [*.*](*.*)':
            file_filter = '{};;All Files [*.*](*.*)'.format(file_filter)
        if for_load and for_dir:
            result_path = QFileDialog.getExistingDirectory(QFileDialog(), caption='Open Directory', directory=str(Path.home()),
                                                           options=QFileDialog.ShowDirsOnly)
        if for_load and not for_dir:
            result_path = QFileDialog.getOpenFileName(QFileDialog(), caption='Open File', directory=str(Path.home()),
                                                      filter=file_filter, options=QFileDialog.ReadOnly)
            result_path = result_path[0]
        if not for_load and not for_dir:
            result_path = QFileDialog.getSaveFileName(QFileDialog(), caption='Save File', directory=str(Path.home()),
                                                      filter=file_filter, options=QFileDialog.ReadOnly)
            result_path = result_path[0]
        if widget_name is not None:
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


class AboutDialog(QDialog):
    def __init__(self, parent) -> None:
        """Moht about dialog window."""
        super().__init__(parent)
        uic.loadUi(f'{utils.here(__file__)}/ui/about.ui', self)
        self.setup_text()

    def setup_text(self) -> None:
        """Prepare text information about Moht application."""
        qt_version = f'{QtCore.PYQT_VERSION_STR} / <b>Qt</b>: {QtCore.QT_VERSION_STR}'
        log_path = path.join(gettempdir(), 'moht.log')
        text = self.label.text().rstrip('</body></html>')
        text += f'<p>Attach log file: {log_path}<br/><br/>'
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
        :param args: Function positional arguments
        :param kwargs: Function keyword arguments
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
