# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Temporary file environment for loading XSD.
"""

from tmEditor import Toolbox

import shutil
import tempfile
import logging
import sys, os

__all__ = ['TempFileEnvironment', ]

class TempFileEnvironment(object):
    """Creates a temprorary directory containing symbolic links to a set
    of required XSD files and other locations and taking care of removing
    the temprary resource. Using this class togetcher with the *width* statement
    guarantees correct removal of temporary resources on excetptions.

        with TempFileEnvironment(filename) as env:
            pass # user actions
    """

    def __init__(self, filename, xsddir = None):
        self._filename = filename
        self._xsddir = xsddir or Toolbox.getXsdDir()
        self.tmpdir = None
        self.cwd = None
        self.create()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.remove()

    @property
    def filename(self):
        """Returns absolute path to filename."""
        return os.path.abspath(self._filename)

    @property
    def xsddir(self):
        """Returns absolute path to XSD files location."""
        return os.path.abspath(self._xsddir)

    @property
    def symlinks(self):
        """Returns tuple containing symbolic links provided by the environment."""
        return (
            (self.filename, os.path.basename(self.filename)),
            (os.path.join(self.xsddir, 'xsd-type'), 'xsd-type'),
            (os.path.join(self.xsddir, 'algorithm.xsd'), 'algorithm.xsd'),
            (os.path.join(self.xsddir, 'bin.xsd'), 'bin.xsd'),
            (os.path.join(self.xsddir, 'cut.xsd'), 'cut.xsd'),
            (os.path.join(self.xsddir, 'ext_signal.xsd'), 'ext_signal.xsd'),
            (os.path.join(self.xsddir, 'ext_signal_set.xsd'), 'ext_signal_set.xsd'),
            (os.path.join(self.xsddir, 'external_requirement.xsd'), 'external_requirement.xsd'),
            (os.path.join(self.xsddir, 'menu.xsd'), 'menu.xsd'),
            (os.path.join(self.xsddir, 'object_requirement.xsd'), 'object_requirement.xsd'),
            (os.path.join(self.xsddir, 'scale_set.xsd'), 'scale_set.xsd'),
            (os.path.join(self.xsddir, 'scale.xsd'), 'scale.xsd'),
        )

    def valid(self):
        """Returns True if virtual environment points to a vaild location."""
        return os.path.isdir(self.tmpdir or '')

    def create(self):
        """Creates a temporary directory, creates symbolic links to the XML and
        XSD files, then loads and validates the menu. Returns a tuple containing
        table objects for menu, scales and external signals.

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
        ...
        """
        self.remove()

        # Get absolute path to source filename.
        filename = os.path.abspath(self.filename)
        xsddir = os.path.abspath(self.xsddir)

        # Create a temporary directory and change current location.
        self.tmpdir = tempfile.mkdtemp()
        logging.debug("created temporary location `%s'", self.tmpdir)
        self.cwd = os.getcwd()
        os.chdir(self.tmpdir)

        # Create symbolic links to XML and XSD files (src, dest).
        for src, dest in self.symlinks:
            os.symlink(src, dest)
            logging.debug("created symbolic link `%s' -> `%s'", dest, src)

    def remove(self):
        """Remove the virtual environment."""
        if not self.valid():
            return

        # Unlink all symbolic links.
        for _, dest in self.symlinks:
            logging.debug("removing symbolic link `%s'", os.path.join(self.tmpdir, dest))
            os.unlink(dest)

        # Change back to current working directory.
        os.chdir(self.cwd)

        # Remove temporary directory.
        logging.debug("removing temporary location `%s'", self.tmpdir)
        shutil.rmtree(self.tmpdir)
        self.tmpdir = None
        self.cwd = None
