"""Application main module."""

import argparse
import logging
import signal
import sys
import os

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from .gui.MainWindow import MainWindow
from . import __version__

def parse_args():
    """Command line argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filenames',
        metavar='<file>',
        nargs='*',
        help="trigger menu XML file",
    )
    parser.add_argument(
        '--timeout',
        metavar='<sec>',
        type=int,
        default=10,
        help="timeout for remote connections in seconds (default 10)",
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        help="increase output verbosity",
    )
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=f"%(prog)s {__version__}",
        help="show the application's version",
    )
    return parser.parse_args()

def main():
    """Main application routine."""
    # Parse arguments.
    args = parse_args()

    # Setup console logging and debug level.
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)

    # As things are getting serious let's start logging to file.
    if args.verbose:
        filename = os.path.expanduser('~/tm-editor.log')
        if os.access(filename, os.W_OK): # is writable?
            handler = logging.FileHandler(filename, mode='a')
            handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            handler.setLevel(level)
            logging.getLogger().addHandler(handler)

    # Diagnostic output.
    logging.debug("PyQt5 version %s", QtCore.QT_VERSION_STR)

    app = QtWidgets.QApplication(sys.argv)

    # Create/Load application settings.
    app.setApplicationName("Trigger Menu Editor")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("HEPHY")
    app.setOrganizationDomain("hephy.at")

    # Init global settings.
    QtCore.QSettings()

    # Create main window.
    window = MainWindow()
    window.setRemoteTimeout(args.timeout)
    window.show()

    # Terminate application on SIG_INT signal.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Run timer to catch SIG_INT signals.
    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    # Load documents from command line (optional).
    def loadDocuments():
        for filename in args.filenames:
            logging.debug("loading file %s", filename)
            window.loadDocument(filename)
    QtCore.QTimer().singleShot(100, loadDocuments)

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
