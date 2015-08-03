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
import json

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

def readSettings(section = None):
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.json')
    with open(filename) as handle:
        settings = json.loads(handle.read())
    return settings[section] if section else settings

# ------------------------------------------------------------------------------
#  String formatting functions
# ------------------------------------------------------------------------------

def fSeparate(text, separator = ' '):
    return ''.join([str(token) for token in (separator, text, separator)])

def fAlgorithm(expr):
    return expr
    # """Experimental HTML syntax highlighting for algorithm expressions."""
    # expr = formatter.humanize(expr)
    # if len(expr) > 20:
    #     expr = expr[:17] + "..."
    # for function in ('comb', 'dist', 'mass'):
    #     expr = expr.replace('{0}'.format(function), '<span style="color: blue; font-weight: bold;">{0}</span>'.format(function))
    # for op in ('AND', 'OR', 'NOT'):
    #     expr = expr.replace(' {0} '.format(op), ' <span style="color: darkblue; font-weight: bold;">{0}</span> '.format(op))
    # return expr

def fCut(value):
    try:
        return format(float(value), '+.3f')
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
