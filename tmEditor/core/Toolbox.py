# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Toolbox containing various helpers.
"""

import tmGrammar

from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter

from PyQt4 import QtCore
from PyQt4 import QtGui

import re
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

def getXsdDir():
    """Returns path for XSD files."""
    try:
        return getenv('UTM_XSD_DIR')
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

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """Natural string sorting.
    >>> sorted("100 10 3b 2 1".split(), key=natural_sort_key)
    ['1', '2', '3b', '10', '100']
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, str(s))]

# ------------------------------------------------------------------------------
#  String formatting functions
# ------------------------------------------------------------------------------

def fSeparate(text, separator=' '):
    return ''.join([str(token) for token in (separator, text, separator)])

def fAlgorithm(expression):
    return AlgorithmFormatter.normalize(expression)

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

def fCounts(value):
    value = str(value).replace('p', '.') # Replace 'p' by comma.
    return "{0:.0f} counts".format(float(value))

def fComparison(value):
    """Retruns formatted thresold comparisons signs."""
    return {
        tmGrammar.EQ: "==",
        tmGrammar.GE: ">=",
        tmGrammar.GT: ">",
        tmGrammar.LE: "<=",
        tmGrammar.LT: "<",
        tmGrammar.NE: "!=",
    }[str(value)]

def fBxOffset(value):
    """Retruns formatted BX offset."""
    return '0' if int(value) == 0 else format(int(value), '+d')

# -----------------------------------------------------------------------------
#  Icon factories
# -----------------------------------------------------------------------------

def createIcon(name):
    """Factory function, creates a multi resolution gnome theme icon."""
    if hasattr(QtGui.QIcon, "fromTheme"):
        icon = QtGui.QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    icon = QtGui.QIcon()
    for root, dirs, files in os.walk("/usr/share/icons/gnome"):
        for file in files:
            if name == os.path.splitext(os.path.basename(file))[0]:
                icon.addFile(os.path.join(root, file))
    if not len(icon.availableSizes()):
        filename = ":/icons/{name}.svg".format(**locals())
        if QtCore.QFile.exists(filename):
            icon.addFile(filename)
        filename = ":/icons/16/{name}.svg".format(**locals())
        if QtCore.QFile.exists(filename):
            icon.addPixmap(QtGui.QPixmap(filename))
        filename = ":/icons/24/{name}.svg".format(**locals())
        if QtCore.QFile.exists(filename):
            icon.addPixmap(QtGui.QPixmap(filename))
    return icon

def miniIcon(name, size=13):
    """Returns mini icon to be used for items in list and tree views."""
    return QtGui.QIcon(QtGui.QIcon(":/icons/{name}.svg".format(name=name)).pixmap(size, size))

# -----------------------------------------------------------------------------
#  Cut settings class
# -----------------------------------------------------------------------------

class CutSpecification(object):
    """Cut specific settings."""

    def __init__(self, name, object, type, objects=None, range_precision=None,
                 range_step=None, range_unit=None, data=None, data_exclusive=False,
                 title=None, description=None, enabled=True):
        self.name = name
        self.object = object
        self.type = type
        self.objects = objects or []
        self.range_precision = int(range_precision or 0)
        self.range_step = float(range_step or 0.)
        self.range_unit = range_unit or ""
        self.data = data or {}
        self.data_exclusive = data_exclusive or False
        self.title = title or ""
        self.description = description or ""
        self.enabled = enabled

    @property
    def data_sorted(self):
        """Returns sorted list of data dict values."""
        return [self.data[key] for key in sorted(self.data.keys())]
