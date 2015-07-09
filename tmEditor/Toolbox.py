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

# ------------------------------------------------------------------------------
#  String formatting functions
# ------------------------------------------------------------------------------

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
    return format(float(value), '+.3f')

def fThreshold(value):
    value = str(value).replace('p', '.') # Replace 'p' by comma.
    return "{0:.1f} GeV".format(float(value))

def fComparison(value):
    return str(value).strip('.')

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

# TODO transitional resource fetcher
def resource(filename):
    root = getenv('UTM_ROOT')
    return os.path.abspath("{root}/tmEditor/resource/{filename}".format(**locals()))
