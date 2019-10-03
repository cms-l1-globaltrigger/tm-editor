from tmEditor.core import XmlDecoder, XmlEncoder, Settings
from tmEditor.core.RemoteVersionInfo import RemoteVersionInfo
from tmEditor import __version__

from distutils.version import StrictVersion
from distutils.spawn import find_executable

import argparse
import logging
import signal
import sys, os

from PyQt5 import QtCore, QtWidgets

from tmEditor.gui.MainWindow import MainWindow

EXIT_OK = 0
EXIT_FAIL = 1

kApplication = 'application'
kVersion = 'version'

def parse():
    """Command line argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames',
        metavar = '<file>',
        nargs = '*',
        help = "trigger menu XML file",
    )
    parser.add_argument('--export-xml',
        metavar = '<file>',
        help = "export normalized document to XML file",
    )
    parser.add_argument('--timeout',
        metavar = '<sec>',
        type = int,
        default = 10,
        help = "timeout for remote connections in seconds (default 10)",
    )
    parser.add_argument('--no-update-check',
        action = 'store_true',
        help = "do not check for application updates using a remote server",
    )
    parser.add_argument('-v', '--verbose',
        action = 'count',
        help = "increase output verbosity",
    )
    parser.add_argument('-V', '--version',
        action = 'version',
        version = "%(prog)s {}".format(__version__),
        help = "show the application's version",
    )
    return parser.parse_args()

def export_xml(args):
    """Export normalized document to XML file."""
    if not args.export_xml:
        message = "argument `--export-xml' requires a XML file to be loaded"
        raise RuntimeError(message)
    if not args.filenames:
        message = "argument `--export-xml' requires a XML file to be loaded"
        raise RuntimeError(message)
    menu = XmlDecoder.load(args.filenames[0])
    XmlEncoder.dump(menu, args.export_xml)
    return EXIT_OK

def dump_information(args):
    """Dump menu information."""
    if not args.filenames:
        logging.error("missing filename argument")
        return EXIT_FAIL
    for filename in args.filenames:
        try:
            menu = XmlDecoder.load(filename)
            logging.info("filename: %s", filename)
            logging.info("name: %s", menu.menu.name)
            logging.info("comment: %s", menu.menu.comment)
            logging.info("UUID menu: %s", menu.menu.uuid_menu)
            logging.info("grammar version: %s", menu.menu.grammar_version)
            logging.info("scale set: %s", menu.scales.scaleSet['name'])
            logging.info("external signal set: %s", menu.extSignals.extSignalSet['name'])
            logging.info("algorithms: %s", len(menu.algorithms))
        except RuntimeError as e:
            logging.error(message)
        return EXIT_FAIL
    return EXIT_OK

def bootstrap(args):
    """Bootstrap core application."""

    # Setup console logging and debug level.
    loggingLevel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=loggingLevel)

    # As things are getting serious let's start logging to file.
    if args.verbose:
        filename = os.path.expanduser('~/tm-editor.log')
        if os.access(filename, os.W_OK): # is writable?
            handler = logging.FileHandler(filename, mode='a')
            handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            handler.setLevel(loggingLevel)
            logging.getLogger().addHandler(handler)

    # Diagnostic output.
    logging.debug("launching L1-Trigger Menu Editor")
    logging.debug("version %s", __version__)
    logging.debug("__file__='%s'", __file__)
    logging.debug("sys.argv='%s'", " ".join(sys.argv))
    logging.debug("LD_LIBRARY_PATH='%s'", os.getenv('LD_LIBRARY_PATH'))
    logging.debug("PATH='%s'", os.getenv('HOME'))
    logging.debug("UTM_ROOT='%s'", os.getenv('UTM_ROOT'))
    logging.debug("UTM_XSD_DIR='%s'", os.getenv('UTM_XSD_DIR'))
    logging.debug("LC_ALL='%s'", os.getenv('LC_ALL'))
    logging.debug("python version %s.%s.%s", *sys.version_info[:3])

def main():
    """Main application routine."""
    # Parse arguments.
    args = parse()
    bootstrap(args)

    # Export options
    if args.export_xml:
        return export_xml(args)

    # Create application window.
    try:
        # Diagnostic output.
        logging.debug("PyQt5 version %s", QtCore.QT_VERSION_STR)

        app = QtWidgets.QApplication(sys.argv)

        # Create/Load application settings.
        app.setOrganizationName("HEPHY")
        app.setOrganizationDomain("hephy.at")
        app.setApplicationName("Trigger Menu Editor")

        # Init global settings.
        QtCore.QSettings()

        # Create main window.
        window = MainWindow()
        window.setRemoteTimeout(args.timeout)
        window.show()

        # Load documents from command line (optional).
        for filename in args.filenames:
            logging.debug("loading file %s", filename)
            window.loadDocument(filename)
            app.processEvents()

        # Terminate application on SIG_INT signal.
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Run timer to catch SIG_INT signals.
        timer = QtCore.QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

        return app.exec_()
    except RuntimeError as message:
        logging.error(message)
        return EXIT_FAIL
    return EXIT_OK

if __name__ == '__main__':
    sys.exit(main())
