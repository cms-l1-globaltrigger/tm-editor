"""Application main module."""

import argparse
import logging
import signal
import sys
import os

import PyQt5
from PyQt5 import QtCore, QtWidgets

from . import __version__
from .application import Application


def parse_args() -> argparse.Namespace:
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


def main() -> None:
    """Main application routine."""
    # Parse arguments.
    args = parse_args()

    # Setup console logging and debug level.
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)

    # Diagnostic output.
    logging.debug("%s version %s", PyQt5.__name__, QtCore.QT_VERSION_STR)

    app = Application()
    app.setRemoteTimeout(args.timeout)
    app.loadSettings()

    # Load documents from command line (optional).
    def loadDocuments():
        for filename in args.filenames:
            logging.debug("loading file %s", filename)
            app.loadDocument(filename)
    QtCore.QTimer().singleShot(100, loadDocuments)  # ignore: type

    app.eventLoop()
    app.storeSettings()


if __name__ == '__main__':
    main()
