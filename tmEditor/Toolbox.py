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
import tmGrammar
from AlgorithmFormatter import AlgorithmFormatter

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import uuid
import shutil
import tempfile
import logging
import sys, os
import json, re
from operator import attrgetter

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

# ------------------------------------------------------------------------------
#  String formatting functions
# ------------------------------------------------------------------------------

def fSeparate(text, separator = ' '):
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

def createIcon(name):
    """Factory function, creates a multi resolution gnome theme icon."""
    if hasattr(QIcon, "fromTheme"):
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    icon = QIcon()
    for root, dirs, files in os.walk("/usr/share/icons/gnome"):
        for file in files:
            if name == os.path.splitext(os.path.basename(file))[0]:
                icon.addFile(os.path.join(root, file))
    if not len(icon.availableSizes()):
        filename = ":/icons/{name}.svg".format(**locals())
        if QFile.exists(filename):
            icon.addFile(filename)
        filename = ":/icons/16/{name}.svg".format(**locals())
        if QFile.exists(filename):
            icon.addPixmap(QPixmap(filename))
        filename = ":/icons/24/{name}.svg".format(**locals())
        if QFile.exists(filename):
            icon.addPixmap(QPixmap(filename))
    return icon

# -----------------------------------------------------------------------------
#  Common widgets
# -----------------------------------------------------------------------------

class StockColors:
    """Set of common colors for the main application."""
    LightGreen = "#8be230"
    Yellow     = "#ffe230"
    LightRed   = "#ff443f"
    Green      = "#579515"
    DarkYellow = "#bea500"
    Red        = "#c60500"
    LightBlue  = "#0066ff"
    LightGray  = "#c0c0c0"

# -----------------------------------------------------------------------------
#  A framed color icon box.
# -----------------------------------------------------------------------------

class ColorIcon(QFrame):
    """Provides an fixed sized framed color icon for building color labeled legends.

    The default square size is 12 pixel.
    """
    def __init__(self, color, parent = None, size = 12):
        super(ColorIcon, self).__init__(parent)
        # Fix the icon size.
        self.setFixedSize(size, size)
        # Draw a border around the icon.
        self.setFrameShape(self.Box)
        self.setFrameShadow(self.Plain)
        # Make sure background color is displayed.
        self.setAutoFillBackground(True)
        # Store the icon's color.
        self.setColor(color)

    def setColor(self, color):
        # Store the icon's color.
        self.color = QColor(color)
        # Setup the active color background brush.
        palette = self.palette()
        brush = QBrush(self.color)
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Window, brush)
        palette.setBrush(QPalette.Active, QPalette.Light, brush) # Bugfix for parent widgets with background role: Light.
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Light, brush)
        self.setPalette(palette)

# -----------------------------------------------------------------------------
#  Legend label with color icon on the right.
# -----------------------------------------------------------------------------

class ColorLabel(QWidget):
    """Color legend with icon and text label on the left."""

    def __init__(self, color, text, parent = None):
        super(ColorLabel, self).__init__(parent)
        # Create the icon and the text label.
        self.icon = ColorIcon(color, self)
        self.label = QLabel(text, self)
        # Setup the layout.
        layout = QHBoxLayout()
        layout.addWidget(self.icon)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def setColor(self, color):
        self.icon.setColor(color)

    def setText(self, text):
        self.label.setText(text)

# -----------------------------------------------------------------------------
#  Legend label with icon on the right.
# -----------------------------------------------------------------------------

class IconLabel(QWidget):
    """label with 16x16 pixel icon and text label on the left."""

    def __init__(self, icon, text, parent = None):
        """Set icon of type QIcon and a text message."""
        super(IconLabel, self).__init__(parent)
        # Create the icon and the text label.
        self.icon = QLabel(self)
        self.icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setIcon(icon)
        self.label = QLabel(text, self)
        self.icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Setup the layout.
        layout = QHBoxLayout()
        layout.addWidget(self.icon)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def setIcon(self, icon):
        """Set displayed icon."""
        self.icon.setPixmap(icon.pixmap(16, 16))

    def setText(self, text):
        """Set displayed text."""
        self.label.setText(str(text))

# -----------------------------------------------------------------------------
#  Read only line edit widget.
# -----------------------------------------------------------------------------

class ReadOnlyLineEdit(QLineEdit):
    """Customized rad only line edit."""

    def __init__(self, text, parent = None):
        """
        @param text the initial text to display.
        @param parent optional parent widget.
        """
        super(ReadOnlyLineEdit, self).__init__(str(text), parent)
        self.setReadOnly(True)
        # Set background to parent widget background.
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Base, palette.color(QtGui.QPalette.Window))
        self.setPalette(palette)

# -----------------------------------------------------------------------------
#  Restricted line edit widget.
# -----------------------------------------------------------------------------

class RestrictedLineEdit(QLineEdit):
    """Restricted line edit widget.

    An optional prefix can be defined, it is part of the input but can not be
    edited or removed by the user. An optional regular expression prevents
    invalid user input (characters) also a maximum length of the full input
    can be defined.
    """

    def __init__(self, parent = None):
        """Widget's constructor.

        @param parent optional parent widget.
        """
        super(RestrictedLineEdit, self).__init__(parent)
        # Optional prefix.
        self._prefix = None
        # Optional regular expression pattern.
        self._pattern = None
        # Guard all user input changes.
        self.textChanged.connect(self.validate)

    def setPrefix(self, prefix):
        """Set a fixed value prefix."""
        self._prefix = str(prefix)
        self.validate()

    def prefix(self):
        """@returns prefix, None if not set."""
        return self._prefix

    def setRegexPattern(self, pattern):
        """Set regular expression pattern to guard user input."""
        self.setValidator(QRegExpValidator(QRegExp(str(pattern)), self))

    def validate(self):
        """Validate user input."""
        if self._prefix and self.text().length() < len(self._prefix):
            # Make it impossible to remove the L1Menu_ prefix.
            self.textChanged.disconnect()
            self.setText(self._prefix)
            self.textChanged.connect(self.validate)

# -----------------------------------------------------------------------------
#  Restricted plain text edit.
# -----------------------------------------------------------------------------

class RestrictedPlainTextEdit(QPlainTextEdit):
    """Restricted plain text edit widget. Maximum length can be specified.
    """
    def __init__(self, parent = None):
        super(RestrictedPlainTextEdit, self).__init__(parent)
        self._maxLength = None
        self.textChanged.connect(self.validate)
        self.setTabChangesFocus(True)

    def setMaxLength(self, length):
        """Set maximal input length."""
        self._maxLength = int(length)

    def maxLength(self):
        """@returns maximal input length."""
        return int(self._maxLength)

    def validate(self):
        """Validate user input."""
        if self._maxLength:
            if self.toPlainText().length() > self._maxLength:
                self.textCursor().deletePreviousChar()

class ListSpinBox(QSpinBox):
    """Custom spin box for a list of integers."""

    def __init__(self, values, parent = None):
        super(ListSpinBox, self).__init__(parent)
        self.setValues(values)

    def setValues(self, values):
        self.values = [int(value) for value in values]
        self.index = 0
        minimum = min(self.values)
        maximum = max(self.values)
        self.setRange(minimum, maximum)

    def stepBy(self, steps):
        self.index += steps
        self.setValue(int(self.values[self.index]))

    def value(self, index = None):
        """Returns bins floating point value by LUT index (upper or lower depending on mode)."""
        if index == None: index = self.index
        return self.values[index]

    def minimum(self):
        return self.value(0)

    def maximum(self):
        return self.value(-1)

    def setValue(self, value):
        value = self.nearest(value)
        super(ListSpinBox, self).setValue(value)

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        return self.nearest(int(str(text).strip(" =<>!")))

    def nearest(self, value):
        """Returns nearest neighbor of value in range."""
        # See also "finding index of an item closest to the value in a list that's not entirely sorted"
        # http://stackoverflow.com/questions/9706041/finding-index-of-an-item-closest-to-the-value-in-a-list-thats-not-entirely-sort
        result = min(range(len(self.values)), key = lambda i: abs(self.values[i] - value))
        self.index = result
        return self.value(self.index)
