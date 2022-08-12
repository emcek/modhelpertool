import signal
import sys
import tkinter as tk
from argparse import ArgumentParser, RawTextHelpFormatter
from os import path

from PyQt5 import QtCore
from PyQt5.QtCore import QLibraryInfo, QTranslator, QLocale
from PyQt5.QtWidgets import QApplication

from moht import VERSION, tkgui, qtgui


def run_tk():
    """Function to start Mod Helper Tool Tk GUI."""
    root = tk.Tk()
    width, height = 500, 230
    root.title('Mod Helper Tool')
    root.geometry(f'{width}x{height}')
    root.minsize(width=width, height=height)
    root.iconphoto(False, tk.PhotoImage(file=join(abspath(dirname(__file__)), 'img', 'moht.png')))
    window = tkgui.MohtTkGui(master=root)
    window.mainloop()
    root.iconphoto(False, tk.PhotoImage(file=path.join(path.abspath(path.dirname(__file__)), 'img', 'moht.png')))
    window = tkgui.MohtTkGui(master=root)
    window.mainloop()


def run_qt():
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

    window = qtgui.MohtQtGui()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    parser = ArgumentParser(description='desc', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version='%(prog)s Version: ' + VERSION)
    gui = parser.add_subparsers(title='gui', dest='gui', description='Available subcommands', help='Choose one of GUI')
    gui_qt = gui.add_parser(name='qt', help='Starting Qt5 GUI interface for Moht', formatter_class=RawTextHelpFormatter)
    gui_qt.add_argument('-style', dest='style', help='Style for QtGUI: "fusion" (default) or "windows".', default='fusion')
    gui_tk = gui.add_parser(name='tk', help='Starting Tk GUI interface for Moht', formatter_class=RawTextHelpFormatter)
    args = parser.parse_args()
    if args.gui == 'qt':
        run_qt()
    elif args.gui == 'tk':
        run_tk()
    else:
        parser.print_help()
