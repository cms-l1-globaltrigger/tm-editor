#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from tmEditor.core import XmlDecoder, XmlEncoder, Settings
from tmEditor.core.RemoteVersionInfo import RemoteVersionInfo
from tmEditor.version import VERSION, PKG_RELEASE

from distutils.version import StrictVersion
from distutils.spawn import find_executable

import argparse
import logging
import signal
import sys, os

try:
    # Import PyQt5 modules for graphical operation.
    from tmEditor.PyQt5Proxy import QtCore
    from tmEditor.PyQt5Proxy import QtWidgets
    from tmEditor.PyQt5Proxy import PyQtSignature
    CommandLineMode = False
except ImportError:
    CommandLineMode = True

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
    parser.add_argument('-v', '--verbose',
        action = 'count',
        help = "increase output verbosity",
    )
    parser.add_argument('-V', '--version',
        action = 'version',
        version = "%(prog)s {0}-{1}".format(VERSION, PKG_RELEASE),
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
    logging.debug("version %s-%s", VERSION, PKG_RELEASE)
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

    # Version check
    version_info = RemoteVersionInfo(Settings.VersionUrl)
    if version_info.is_valid:
        if version_info.version > StrictVersion(VERSION):
            version = "{0}.{1}.{2}".format(*version_info.version.version)
            hint = ""
            if find_executable('yum'):
                hint = "via 'apt-get upgrade' or "
            elif find_executable("apt-get"):
                hint = "via 'apt-get upgrade' or "
            logging.info("A new version of tm-editor has been released!")
            logging.info("Version %s is available %sto download at %s", version, hint, Settings.DownloadSite)

            # Download new scales and cabling to cache
            # ... TODO 0.6.0

    # Export options
    if args.export_xml:
        return export_xml(args)

    # End of command line only mode.
    if CommandLineMode:
        return dump_information(args)

    # Create application window.
    try:
        # Diagnostic output.
        logging.debug("%s version %s", PyQtSignature, QtCore.QT_VERSION_STR)

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

        # Version check
        if version_info.is_valid:
            if version_info.version > StrictVersion(VERSION):
                version = "{0}.{1}.{2}".format(*version_info.version.version)
                title = window.tr("New version available")
                hint = window.tr("")
                if find_executable('yum'):
                    hint = window.tr("via <strong>apt-get upgrade</strong> or ")
                elif find_executable("apt-get"):
                    hint = window.tr("via <strong>apt-get upgrade</strong> or ")
                QtWidgets.QMessageBox.information(window,
                    title,
                    window.tr("A new version of tm-editor has been released!<br/><br/>" \
                              "Version {0} is available {1}to download at<br/><br/><a href=\"{2}\">{2}</a>".format(version, hint, Settings.DownloadSite))
                )

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
