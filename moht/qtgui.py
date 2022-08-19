import webbrowser
from functools import partial
from logging import getLogger
from os import path, chdir, remove
from pathlib import Path
from shutil import move, copy2
from sys import version_info, platform
from tempfile import gettempdir
from time import time
from typing import Optional

import qtawesome
from PyQt5 import QtCore, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDialog, QFileDialog

from moht import VERSION, TES3CMD, utils, qtgui_rc

res = qtgui_rc  # prevent to remove import statement accidentally


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
        super(MohtQtGui, self).__init__(flags=QtCore.Qt.Window)
        self.logger = getLogger(__name__)
        uic.loadUi(f'{utils.here(__file__)}/ui/qtgui.ui', self)
        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.logger.debug(f'QThreadPool with {self.threadpool.maxThreadCount()} thread(s)')
        self._le_status = {'le_mods_dir': False, 'le_morrowind_dir': False, 'le_tes3cmd': False}
        self.stats = {'all': 0, 'cleaned': 0, 'clean': 0, 'error': 0, 'time': 0.0}
        self.tes3cmd = TES3CMD[platform]['0_37']
        self._init_menu_bar()
        self._init_buttons()
        self._init_radio_buttons()
        self._init_line_edits()
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
        self.pb_report.clicked.connect(self._pb_report_clicked)
        self.pb_chk_updates.clicked.connect(self._check_updates)

    def _init_line_edits(self):
        self.le_mods_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='le_mods_dir'))
        self.le_morrowind_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='le_morrowind_dir'))
        self.le_tes3cmd.textChanged.connect(partial(self._is_file_exists, widget_name='le_tes3cmd'))
        self._set_le_tes3cmd()
        self.mods_dir = str(Path.home())
        self.morrowind_dir = str(Path.home())

    def _init_radio_buttons(self):
        for ver in ['0_37', '0_40']:
            getattr(self, f'rb_{ver}').toggled.connect(partial(self._rb_tes3cmd_toggled, ver))

    def _rb_tes3cmd_toggled(self, version: str, state: bool) -> None:
        if state:
            self.tes3cmd = TES3CMD[platform][version]
            self._set_le_tes3cmd()

    def _pb_clean_clicked(self) -> None:
        all_plugins = utils.get_all_plugins(mods_dir=self.mods_dir)
        self.logger.debug(f'all_plugins: {len(all_plugins)}: {all_plugins}')
        plugins_to_clean = utils.get_plugins_to_clean(plugins=all_plugins)
        no_of_plugins = len(plugins_to_clean)
        self.logger.debug(f'to_clean: {no_of_plugins}: {plugins_to_clean}')
        req_esm = utils.get_required_esm(plugins=plugins_to_clean)
        self.logger.debug(f'Required esm: {req_esm}')
        missing_esm = utils.find_missing_esm(dir_path=self.mods_dir, data_files=self.morrowind_dir, esm_files=req_esm)
        self.logger.debug(f'Missing esm: {missing_esm}')
        utils.copy_filelist(missing_esm, self.morrowind_dir)
        chdir(self.morrowind_dir)
        self.stats = {'all': no_of_plugins, 'cleaned': 0, 'clean': 0, 'error': 0}
        start = time()
        for idx, plug in enumerate(plugins_to_clean, 1):
            self.logger.debug(f'---------------------------- {idx} / {no_of_plugins} ---------------------------- ')
            self.logger.debug(f'Copy: {plug} -> {self.morrowind_dir}')
            copy2(plug, self.morrowind_dir)
            mod_file = utils.extract_filename(plug)
            out, err = utils.run_cmd(f'{self.tes3cmd} clean --output-dir --overwrite "{mod_file}"')
            result, reason = utils.parse_cleaning(out, err, mod_file)
            self.logger.debug(f'Result: {result}, Reason: {reason}')
            self._update_stats(mod_file, plug, reason, result)
            if self.cb_rm_bakup.isChecked():
                mod_path = path.join(self.morrowind_dir, mod_file)
                self.logger.debug(f'Remove: {mod_path}')
                remove(mod_path)
        self.logger.debug(f'---------------------------- Done: {no_of_plugins} ---------------------------- ')
        if self.cb_rm_cache.isChecked():
            cachedir = 'tes3cmd' if platform == 'win32' else '.tes3cmd-3'
            utils.rm_dirs_with_subdirs(dir_path=self.morrowind_dir, subdirs=['1', cachedir])
        utils.rm_copied_extra_esm(missing_esm, self.morrowind_dir)
        cleaning_time = time() - start
        self.stats['time'] = cleaning_time
        self.logger.debug(f'Total time: {cleaning_time} s')
        self.statusbar.showMessage('Done. See report!')
        self.pb_report.setEnabled(True)

    def _pb_report_clicked(self) -> None:
        """Show report after clean-up."""
        self.logger.debug(f'Report: {self.stats}')
        report = f'Detected plugins to clean: {self.stats["all"]}\n'
        report += f'Already clean plugins: {self.stats["clean"]}\n'
        report += f'Cleaned plugins: {self.stats["cleaned"]}\n'
        report += '\n'.join([f'Error {k}: {self.stats[k]}' for k in self.stats if 'not found' in k])
        report += '\n\nCopy missing esm file(s) to Data Files directory and clean again.\n\n' if 'Error' in report else '\n'
        report += f'Total time: {self.stats["time"]:.2f} s'
        self._show_message_box(kind_of='information', title='Cleaning Report', message=report)
        self.pb_report.setEnabled(False)
        self.statusbar.showMessage(f'ver. {VERSION}')

    def _check_updates(self):
        latest, desc = utils.is_latest_ver(package='moht', current_ver=VERSION)
        current_ver = 'No updates' if latest else f'Update available: {desc}'
        self.statusbar.showMessage(f'ver. {VERSION} - {current_ver}')

    def _set_le_tes3cmd(self) -> None:
        self.tes3cmd = path.join(utils.here(__file__), 'resources', self.tes3cmd)

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

    def _check_clean_bin(self,) -> bool:
        self.logger.debug('Checking tes3cmd')
        out, err = utils.run_cmd(f'{self.tes3cmd} -h')
        result, reason = utils.parse_cleaning(out, err, '')
        self.logger.debug(f'Result: {result}, Reason: {reason}')
        if not result:
            self.statusbar.showMessage(f'Error: {reason}')
            msg = ''
            if 'Config::IniFiles' in reason:
                msg = 'Use package manager, check for `perl-Config-IniFiles` or a similar package.\n\nOr run from a terminal:\ncpan install Config::IniFiles'
            elif 'Not tes3cmd' in reason:
                msg = 'Selected file is not a valid tes3cmd executable.\n\nPlease select a correct binary file.'
            self._show_message_box(kind_of='warning', title='Not tes3cmd', message=msg)
        return result

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
        super(AboutDialog, self).__init__(parent)
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
