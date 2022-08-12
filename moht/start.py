import signal
import sys
import tkinter as tk
from os import path

from PyQt5 import QtCore
from PyQt5.QtCore import QLibraryInfo, QTranslator, QLocale
from PyQt5.QtWidgets import QApplication

from moht.qtgui import QtGui
from moht.tk_gui import MohtTkGui


def run():
    """Function to start Mod Helper Tool GUI."""
    root = tk.Tk()
    width, height = 500, 230
    root.title('Mod Helper Tool')
    root.geometry(f'{width}x{height}')
    root.minsize(width=width, height=height)
    root.iconphoto(False, tk.PhotoImage(file=path.join(path.abspath(path.dirname(__file__)), 'img', 'moht.png')))
    gui = MohtTkGui(master=root)
    gui.mainloop()


def run_qtgui():
    """Function to start Mod Helper Tool QtGUI."""
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)

    translator = QTranslator(app)
    if translator.load(QLocale.system(), 'qtbase', '_', QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
    translator = QTranslator(app)
    if translator.load(QLocale.system(), 'qtgui', '-', path.abspath(path.dirname(__file__))):  # change to _
        app.installTranslator(translator)

    window = QtGui()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_qtgui()
