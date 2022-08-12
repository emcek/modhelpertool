from logging import getLogger
from os import path

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMainWindow

from moht import qtgui_rc

res = qtgui_rc  # prevent to remove import statement accidentally
logger = getLogger(__name__)


def tr(text2translate):
    # return QtCore.QCoreApplication.translate('mw_gui', text2translate)
    return QtCore.QCoreApplication.translate('@default', text2translate)


class QtGui(QMainWindow):
    def __init__(self):
        """Simple initialization"""
        super(QtGui, self).__init__(flags=QtCore.Qt.Window)
        ui__format = '{}/ui/qtgui.ui'.format(path.dirname(path.abspath(__file__)))
        logger.debug(f'Loading UI from {ui__format}')
        uic.loadUi(ui__format, self)
        self.threadpool = QtCore.QThreadPool.globalInstance()
        logger.debug('QThreadPool with {} thread(s)'.format(self.threadpool.maxThreadCount()))
        # self.l_field.setText(self.tr('Field'))
        # self.pb_push.setText(self.tr('Push'))
        # self.l_field.setText(tr('Field'))
        # self.pb_push.setText(tr('Push'))

        # self.show()
