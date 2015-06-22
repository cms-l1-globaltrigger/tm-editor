# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Toolbox containing various helpers.
"""

import tmTable

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import uuid
import shutil
import tempfile
import logging
import sys, os

def getenv(name):
    """Get environment variable. Raises a RuntimeError exception if variable not set."""
    value = os.getenv(name)
    if value is None:
        raise RuntimeError("`{name}' environment not set".format(**locals()))
    return value

def createIcon(category, name):
    """Factory function, creates a multi resolution gnome theme icon."""
    icon = QIcon()
    for size in 16, 24, 32, 64, 128:
        icon.addFile("/usr/share/icons/gnome/{size}x{size}/{category}/{name}.png".format(**locals()))
    return icon

def loadXml(filename, location = getenv('TMGUI_DIR')):
    """Creates a temporary directory, copies the XML and creates symbolic
    links to the XSD files, then loads and validates the menu. Returns a
    tuple containing table objects for menu, scales and external signals.

    XML parsing requires that the XSD files are in the same directory as
    the XML file (this location is actually specified in the XML's header).
    As this prevents to load an XML file at any other location than the XSD
    directory a convenient solution is to create a save temporary directory
    and create a symbolic link to the XML file as well as symbolic links to
    any dependent XSD files. Using only symbolic links does not require to
    copy any file content preserving full data integrity.

    /tmp/tmpPAMK9j/L1Menu_Sample.xml --> /home/user/L1Menu_Sample.xml
    /tmp/tmpPAMK9j/xsd-type --> /usr/shared/utm/xsd-type
    /tmp/tmpPAMK9j/menu.xsd --> /usr/shared/utm/menu.xsd
    """
    logging.debug("Toolbox.loadXml(filename=\"%s\", location=\"%s\")", filename, location)

    # Get absolute path to source filename.
    filename = os.path.abspath(filename)
    logging.debug("loading XML file `%s'", filename)

    # Create a temporary directory and change current location.
    tmpdir = tempfile.mkdtemp()
    logging.debug("created temporary location `%s'", tmpdir)
    cwd = os.getcwd()
    os.chdir(tmpdir)

    # Create symbolic links to XML and XSD files (src, dest).
    symlinks = (
        (filename, os.path.basename(filename)),
        (os.path.join(location, 'xsd-type'), 'xsd-type'),
        (os.path.join(location, 'menu.xsd'), 'menu.xsd'),
    )
    for src, dest in symlinks:
        os.symlink(src, dest)
        logging.debug("created symbolic link `%s' -> `%s'", src, dest)

    # Load tables from XML file.
    menu = tmTable.Menu()
    scale = tmTable.Scale()
    ext_signal = tmTable.ExtSignal()

    logging.debug("reading XML file from `%s'", filename)
    warnings = tmTable.xml2menu(os.path.basename(filename), menu, scale, ext_signal)

    # Unlink all symbolic links.
    for _, dest in symlinks:
        logging.debug("removing symbolic link `%s'", os.path.join(tmpdir, dest))
        os.unlink(dest)

    # Change back to current working directory.
    os.chdir(cwd)

    # Remove temporary directory.
    logging.debug("removing temporary location `%s'", tmpdir)
    shutil.rmtree(tmpdir)

    # Handle errors only after removing the temporary files.
    if warnings:
        raise RuntimeError("Failed to load XML menu {filename}\n{warnings}".format(**locals()))

    return menu, scale, ext_signal

def saveXml(filename, menu, scale, ext_signal, location = getenv('TMGUI_DIR')):
    """Creates a temporary directory, copies the XML and creates symbolic
    links to the XSD files, then loads and validates the menu. Returns a
    tuple containing table objects for menu, scales and external signals.

    XML parsing requires that the XSD files are in the same directory as
    the XML file (this location is actually specified in the XML's header).
    As this prevents to load an XML file at any other location than the XSD
    directory a convenient solution is to create a save temporary directory
    and create a symbolic link to the XML file as well as symbolic links to
    any dependent XSD files. Using only symbolic links does not require to
    copy any file content preserving full data integrity.

    /tmp/tmpPAMK9j/L1Menu_Sample.xml --> /home/user/L1Menu_Sample.xml
    /tmp/tmpPAMK9j/xsd-type --> /usr/shared/utm/xsd-type
    /tmp/tmpPAMK9j/menu.xsd --> /usr/shared/utm/menu.xsd
    """
    logging.debug("Toolbox.saveXml(filename=\"%s\", menu=\"%s\", scale=\"%s\", ext_signal=\"%s\", location=\"%s\")", menu, scale, ext_signal, location)

    # Get absolute path to source filename.
    filename = os.path.abspath(filename)
    logging.debug("writing to XML file `%s'", filename)

    # Create a temporary directory and change current location.
    tmpdir = tempfile.mkdtemp()
    logging.debug("created temporary location `%s'", tmpdir)
    cwd = os.getcwd()
    os.chdir(tmpdir)

    # Create symbolic links to XML and XSD files (src, dest).
    symlinks = (
        (filename, os.path.basename(filename)),
        (os.path.join(location, 'xsd-type'), 'xsd-type'),
        (os.path.join(location, 'menu.xsd'), 'menu.xsd'),
    )
    for src, dest in symlinks:
        os.symlink(src, dest)
        logging.debug("created symbolic link `%s' -> `%s'", src, dest)

    logging.debug("writing XML file to `%s'", filename)
    warnings = tmTable.menu2xml(menu, scale, ext_signal, os.path.basename(filename))

    # Unlink all symbolic links.
    for _, dest in symlinks:
        logging.debug("removing symbolic link `%s'", os.path.join(tmpdir, dest))
        os.unlink(dest)

    # Change back to current working directory.
    os.chdir(cwd)

    # Remove temporary directory.
    logging.debug("removing temporary location `%s'", tmpdir)
    shutil.rmtree(tmpdir)

    # Handle errors only after removing the temporary files.
    if warnings:
        raise RuntimeError("Failed to save XML menu {filename}\n{warnings}".format(**locals()))
