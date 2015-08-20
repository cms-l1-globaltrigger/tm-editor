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
from AlgorithmFormatter import AlgorithmFormatter

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import uuid
import shutil
import tempfile
import logging
import sys, os
import json

Formatter = AlgorithmFormatter()

# ------------------------------------------------------------------------------
#  Low level helper functions
# ------------------------------------------------------------------------------

def getenv(name):
    """Get environment variable. Raises a RuntimeError exception if variable not set."""
    value = os.getenv(name)
    if value is None:
        raise RuntimeError("`{name}' environment not set".format(**locals()))
    return value

def getRootDir():
    return getenv('UTM_ROOT')

def getXsdDir():
    """Returns path for XSD files."""
    try:
        return getenv('TM_EDITOR_XSD_DIR')
    except RuntimeError:
        return os.path.join(getRootDir(), 'tmXsd')

def query(data, **kwargs):
    """Perform dictionary query.
    >>> d = {'foo': 42, 'bar': 'baz'}
    >>> query(d, bar='baz')
    [{'bar': 'baz'}]
    """
    def lookup(entry, **kwargs):
        return sum([entry[key] == value for key, value in kwargs.items()])
    return filter(lambda entry: lookup(entry, **kwargs), data)

def readSettings():
    """Read settings from JSON side file."""
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.json')
    with open(filename) as handle:
        settings = json.loads(handle.read())
    return settings

Settings = readSettings()
"""Storing static settings."""

# ------------------------------------------------------------------------------
#  String formatting functions
# ------------------------------------------------------------------------------

def fSeparate(text, separator = ' '):
    return ''.join([str(token) for token in (separator, text, separator)])

def fAlgorithm(expr):
    """Experimental HTML syntax highlighting for algorithm expressions."""
    expr = Formatter.humanize(expr)
    return expr

def fCut(value):
    try:
        return format(float(value), '+.3f')
    except ValueError:
        return ''

def fHex(value):
    try:
        return '0x{0:x}'.format(int(value))
    except ValueError:
        return ''

def fThreshold(value):
    value = str(value).replace('p', '.') # Replace 'p' by comma.
    return "{0:.1f} GeV".format(float(value))

def fComparison(value):
    return dict(
        eq = "==",
        ge = ">=",
        gt = ">",
        le = "<=",
        lt = "<",
        ne = "!=",
    )[str(value).strip('.')]

def fBxOffset(value):
    return '0' if int(value) == 0 else format(int(value), '+d')

# ------------------------------------------------------------------------------
#  Icon factories
# ------------------------------------------------------------------------------

def createIcon(category, name):
    """Factory function, creates a multi resolution gnome theme icon."""
    icon = QIcon()
    for size in 16, 22, 24, 32, 64, 128:
        filename = "/usr/share/icons/gnome/{size}x{size}/{category}/{name}.png".format(**locals())
        if os.path.isfile(filename):
            icon.addFile(filename)
    return icon
