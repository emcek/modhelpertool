#!/usr/bin/env python
import signal
import sys
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from logging import getLogger
from os import name
from os import path
from platform import architecture, uname, python_implementation, python_version
from sys import platform
from tempfile import gettempdir

from moht import VERSION
from moht.log import config_logger
from moht.utils import here

logger = getLogger(f'moht.{__name__}')


def run_tk():
    """Function to start Mod Helper Tool Tk GUI."""
    import tkinter
    from moht.tkgui import MohtTkGui

    root = tkinter.Tk()
    width, height = 500, 280
    root.title('Mod Helper Tool')
    root.geometry(f'{width}x{height}')
    root.minsize(width=width, height=height)
    root.iconphoto(False, tkinter.PhotoImage(file=path.join(here(__file__), 'img', 'moht.png')))
    try:
        window = MohtTkGui(master=root)
        window.mainloop()
    except Exception as exp:
        logger.exception(f'Critical error: {exp}')


def run_qt():
    """Function to start Mod Helper Tool QtGUI."""
    from PyQt5 import QtCore
    from PyQt5.QtCore import QLibraryInfo, QTranslator, QLocale
    from PyQt5.QtWidgets import QApplication
    from moht.qtgui import MohtQtGui

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)

    translator = QTranslator(app)
    if translator.load(QLocale.system(), 'qtbase', '_', QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
    translator = QTranslator(app)
    if translator.load(QLocale.system(), 'qtgui', '-', here(__file__)):  # change to _
        app.installTranslator(translator)

    try:
        window = MohtQtGui()
        window.show()
    except Exception as exp:
        logger.exception(f'Critical error: {exp}')
    sys.exit(app.exec())


def run(cli_opts: Namespace) -> None:
    """
    Function to start selected GUI of Mod Helper Tool.

    :param cli_opts: arguments from CLI
    """
    config_logger(verbose=cli_opts.verbose, quiet=cli_opts.quiet)
    logger.info(f'Log file stored at: {path.join(gettempdir(), "moht.log")}')
    logger.info(f'moht v{VERSION} https://gitlab.com/modding-openmw/modhelpertool')
    logger.debug(f'Arch: {name} / {platform} / {" / ".join(architecture())}')
    logger.debug(f'Python: {python_implementation()}-{python_version()}')
    logger.debug(f'{uname()}')
    globals()[f'run_{cli_opts.gui}']()


if __name__ == '__main__':
    parser = ArgumentParser(description='Simple yet powerful tool to help you manage your mods in several ways.', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version='%(prog)s Version: ' + VERSION)
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', default=False, help='be quiet')
    parser.add_argument('-v', '--verbose', action='count', dest='verbose', default=0, help='increase output verbosity')
    gui = parser.add_subparsers(title='gui', dest='gui', description='Available subcommands', help='choose one of GUI')
    gui_qt = gui.add_parser(name='qt', help='starting Qt5 GUI interface for Moht', formatter_class=RawTextHelpFormatter)
    gui_qt.add_argument('-style', dest='style', help='style for QtGUI: "fusion" (default) or "windows".', default='fusion')
    gui_tk = gui.add_parser(name='tk', help='starting Tk GUI interface for Moht', formatter_class=RawTextHelpFormatter)
    args = parser.parse_args()
    if args.gui:
        run(args)
    else:
        parser.print_help()
