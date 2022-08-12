from functools import partial
from logging import getLogger
from os import path
from sys import version_info

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDialog
from moht import VERSION

from moht import qtgui_rc

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


class QtGui(QMainWindow):
    def __init__(self) -> None:
        """Simple initialization."""
        super(QtGui, self).__init__(flags=QtCore.Qt.Window)
        ui__format = f'{here}/ui/qtgui.ui'
        logger.debug(f'Loading UI from {ui__format}')
        uic.loadUi(ui__format, self)
        self.threadpool = QtCore.QThreadPool.globalInstance()
        logger.debug('QThreadPool with {} thread(s)'.format(self.threadpool.maxThreadCount()))
        # self.l_field.setText(self.tr('Field'))
        # self.pb_push.setText(self.tr('Push'))
        # self.l_field.setText(tr('Field'))
        # self.pb_push.setText(tr('Push'))
        self.init_menu_bar()

    def init_menu_bar(self) -> None:
        """Initialization of menubar."""
        self.actionQuit.triggered.connect(self.close)
        self.actionAboutMoht.triggered.connect(AboutDialog(self).open)
        self.actionAboutQt.triggered.connect(partial(self._show_message_box, kind_of='aboutQt', title='About Qt'))

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
    """Moht about dialog window."""
    def __init__(self, parent) -> None:
        """Simple initialization."""
        super(AboutDialog, self).__init__(parent)
        uic.loadUi(f'{here}/ui/about.ui', self)
        self.setup_text()

    def setup_text(self) -> None:
        """Prepare text information about Moht application."""
        qt_version = f'{QtCore.PYQT_VERSION_STR} / <b>Qt</b>: {QtCore.QT_VERSION_STR}'
        text = self.label.text().rstrip('</body></html>')
        text += f'<p><b>moht:</b> {VERSION}'
        text += '<br><b>python:</b> {0}.{1}.{2}-{3}.{4}'.format(*version_info)
        text += f'<br><b>PyQt:</b> {qt_version}</p></body></html>'
        self.label.setText(text)
