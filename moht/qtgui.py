from functools import partial
from logging import getLogger
from os import path
from pathlib import Path
from sys import version_info, platform
from tempfile import gettempdir
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDialog, QFileDialog

from moht import VERSION, qtgui_rc

res = qtgui_rc  # prevent to remove import statement accidentally
logger = getLogger(__name__)
here = path.dirname(path.abspath(__file__))


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
        ui__format = f'{here}/ui/qtgui.ui'
        logger.debug(f'Loading UI from {ui__format}')
        uic.loadUi(ui__format, self)
        self.threadpool = QtCore.QThreadPool.globalInstance()
        logger.debug(f'QThreadPool with {self.threadpool.maxThreadCount()} thread(s)')
        # self.l_field.setText(self.tr('Field'))
        # self.pb_push.setText(self.tr('Push'))
        # self.l_field.setText(tr('Field'))
        # self.pb_push.setText(tr('Push'))
        self._le_status = {'le_mods_dir': False, 'le_morrowind_dir': False, 'le_test3cmd': False}
        self._init_menu_bar()
        self._init_buttons()
        self._init_line_edits()

    def _init_menu_bar(self) -> None:
        self.actionQuit.triggered.connect(self.close)
        self.actionAboutMoht.triggered.connect(AboutDialog(self).open)
        self.actionAboutQt.triggered.connect(partial(self._show_message_box, kind_of='aboutQt', title='About Qt'))

    def _init_buttons(self) -> None:
        self.pb_mods_dir.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=True, widget_name='le_mods_dir'))
        self.pb_morrowind_dir.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=True, widget_name='le_morrowind_dir'))
        self.pb_test3cmd.clicked.connect(partial(self._run_file_dialog, for_load=True, for_dir=False, widget_name='le_test3cmd'))
        self.pb_clean.clicked.connect(self._pb_clean_clicked)
        self.pb_report.clicked.connect(self._pb_pb_report_clicked)

    def _init_line_edits(self):
        self.le_mods_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='le_mods_dir'))
        self.le_morrowind_dir.textChanged.connect(partial(self._is_dir_exists, widget_name='le_morrowind_dir'))
        self.le_test3cmd.textChanged.connect(partial(self._is_file_exists, widget_name='le_test3cmd'))

        tes3cmd = 'tes3cmd-0.37v.exe' if platform == 'win32' else 'tes3cmd-0.37w'
        self.le_test3cmd.setText(path.join(here, 'resources', tes3cmd))

        if platform == 'linux':
            self.le_mods_dir.setText('/home/emc/CitiesTowns/')
            self.le_morrowind_dir.setText('/home/emc/.wine/drive_c/Morrowind/Data Files/')
        elif platform == 'win32':
            self.le_mods_dir.setText('D:/CitiesTowns')
            self.le_morrowind_dir.setText('S:/Program Files/Morrowind/Data Files')
        else:
            self.le_mods_dir.setText(str(Path.home()))
            self.le_morrowind_dir.setText(str(Path.home()))

    def _pb_clean_clicked(self) -> None:
        pass

    def _pb_pb_report_clicked(self) -> None:
        pass

    def _is_dir_exists(self, text: str, widget_name: str) -> None:
        dir_exists = path.isdir(text)
        logger.debug(f'Path: {text} for {widget_name} exists: {dir_exists}')
        self._line_edit_handling(widget_name, dir_exists)

    def _is_file_exists(self, text: str, widget_name) -> None:
        file_exists = path.isfile(text)
        logger.debug(f'Path: {text} for {widget_name} exists: {file_exists}')
        self._line_edit_handling(widget_name, file_exists)

    def _line_edit_handling(self, widget_name: str, path_exists: bool) -> None:
        """
        Mark text of LieEdit as red if path does not exist.

        Additionally, save status and enable /disable Clean button base on it.

        :param widget_name: widget name
        :param path_exists: bool for path existence
        """
        if not path_exists:
            getattr(self, widget_name).setStyleSheet('color: red;')
        else:
            getattr(self, widget_name).setStyleSheet('')
        self._le_status[widget_name] = path_exists
        if all(self._le_status.values()):
            self.pb_clean.setEnabled(True)
        else:
            self.pb_clean.setEnabled(False)

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


class AboutDialog(QDialog):
    def __init__(self, parent) -> None:
        """Moht about dialog window."""
        super(AboutDialog, self).__init__(parent)
        uic.loadUi(f'{here}/ui/about.ui', self)
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
