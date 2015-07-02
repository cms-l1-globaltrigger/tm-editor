# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Menu container, wrapping tmTable and XML bindings.
"""

import tmTable

from tmEditor import Toolbox

import uuid
import shutil
import tempfile
import logging
import sys, os

__all__ = ['Menu', ]

class Menu(object):

    def __init__(self, filename = None):
        self.menu = []
        self.algorithms = []
        self.cuts = []
        self.objects = []
        self.scales = None
        self.externals = None
        if filename:
            self.loadXml(filename)

    def addObject(self, name, offset = 0):
        """Provided for convenience."""
        self.objects.append(dict(
            name = name,
            bx_offset = offset,
        ))

    def addCut(self, name, minimum, maximum):
        """Provided for convenience."""
        self.objects.append(dict(
            name = name,
            minimum = minimum,
            maximum = maximum,
        ))

    def addAlgorithm(self, name, expression):
        """Provided for convenience."""
        self.objects.append(dict(
            name = name,
            expression = expression,
        ))

    def loadXml(self, filename):
        """Provided for convenience."""
        menu, scale, ext_signal = loadXml(filename)
        self.menu = dict(menu.menu.items())
        self.algorithms = [dict(algorithm) for algorithm in menu.algorithms]
        buffer = []
        for cuts in menu.cuts.values():
            for cut in cuts:
                cut = dict(cut.items())
                if not cut in buffer:
                    buffer.append(cut)
        self.cuts = buffer
        buffer = []
        for objs in menu.objects.values():
            for obj in objs:
                obj = dict(obj.items())
                if not obj in buffer:
                    buffer.append(obj)
        self.objects = buffer
        self.scales = scale
        self.externals = ext_signal

    def saveXml(self, filename):
        """Provided for convenience."""
        menu = tmTable.Menu()
        for key, value in self.menu.items():
            menu[key] = str(value)
        saveXml(filename, menu, self.scales, self.externals)

# ------------------------------------------------------------------------------
#  TODO take care of creation/destruction of virtual environment by dedicated class.
# ------------------------------------------------------------------------------

def loadXml(filename, location = Toolbox.getenv('TMGUI_DIR')):
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

# ------------------------------------------------------------------------------
#  TODO take care of creation/destruction of virtual environment by dedicated class.
# ------------------------------------------------------------------------------

def saveXml(filename, menu, scale, ext_signal, location = Toolbox.getenv('TMGUI_DIR')):
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
