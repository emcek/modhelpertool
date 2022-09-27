#!/usr/bin/env python
import signal
import sys
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from logging import getLogger
from os import name, path
from platform import architecture, uname, python_implementation, python_version
from tempfile import gettempdir

from PyQt5.QtCore import Qt, QCoreApplication, QLibraryInfo, QLocale, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction

from moht import VERSION
from moht.log import config_logger
from moht.qtgui import MohtQtGui
from moht.utils import here

logger = getLogger(f'moht.{__name__}')
moht_icon = path.join(here(__file__), 'img', 'moht.png')


def run_gui(cli_opts: Namespace) -> None:
    """Function to start Mod Helper Tool QtGUI."""
    config_logger(verbose=cli_opts.verbose, quiet=cli_opts.quiet)
    logger.info(f'Log file stored at: {path.join(gettempdir(), "moht.log")}')
    logger.info(f'moht v{VERSION} https://gitlab.com/modding-openmw/modhelpertool')
    logger.debug(f'Arch: {name} / {sys.platform} / {" / ".join(architecture())}')
    logger.debug(f'Python: {python_implementation()}-{python_version()}')
    logger.debug(f'{uname()}')

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)

    translator = QTranslator(app)
    if translator.load(QLocale.system(), 'qtbase', '_', QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
    translator = QTranslator(app)
    if translator.load(f':translations/i18n/qtgui_{QLocale.system().name()}.qm'):
        app.installTranslator(translator)

    try:
        tray = QSystemTrayIcon()
        tray.setIcon(QIcon(moht_icon))
        tray.setVisible(True)
        tray.setToolTip(f'Moht {VERSION}')
        menu = QMenu()

        window = MohtQtGui(cli_opts)
        window.show()

        check_updates = QAction('Check updates')
        check_updates.triggered.connect(window.check_updates)
        menu.addAction(check_updates)
        action_quit = QAction('Quit')
        action_quit.triggered.connect(app.quit)
        menu.addAction(action_quit)

        tray.setContextMenu(menu)
        tray.activated.connect(window.activated)
        app.aboutToQuit.connect(window.trigger_autosave)
    except Exception as exp:
        logger.exception(f'Critical error: {exp}')
    finally:
        sys.exit(app.exec())


def run() -> None:
    """Function to parse cli parameters and start selected GUI of Mod Helper Tool."""
    parser = ArgumentParser(description='Simple yet powerful tool to help you manage your mods in several ways.', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version='%(prog)s Version: ' + VERSION)
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', default=False, help='be quiet')
    parser.add_argument('-v', '--verbose', action='count', dest='verbose', default=0, help='increase output verbosity')
    parser.add_argument('-y', '--yamlfile', dest='yamlfile', help='Path to configuration YAML file.\nYou can specify relative or absolute path to configuration\nYAML file.')
    parser.add_argument('-style', dest='style', help='style for QtGUI: "fusion" (default) or "windows".', default='fusion')
    args = parser.parse_args()
    run_gui(args)


if __name__ == '__main__':
    run()
