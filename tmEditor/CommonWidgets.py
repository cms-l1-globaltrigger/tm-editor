# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Commonly used helper widgets.

 * PrefixedSpinBox
 * FilterLineEdit
 * RestrictedLineEdit

 * EtaCutChart
 * PhiCutChart
"""

from tmEditor import Toolbox

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import math

#
# Simple overloaded widgets.
#

class PrefixedSpinBox(QSpinBox):
    """A decimal spin box with plus and minus sign prefix.
    Used for assigning bunch crossing offsets.
    """
    def __init__(self, parent = None):
        """Constructur, takes optional reference to parent widget."""
        super(PrefixedSpinBox, self).__init__(parent)

    def textFromValue(self, value):
        return format(value, '+d') # prefix integers also with plus sign

class FilterLineEdit(QLineEdit):
    """Line edit with a clear button on the right side.
    Used for filter and search inputs.
    """
    def __init__(self, parent = None):
        """Constructur, takes optional reference to parent widget."""
        super(FilterLineEdit, self).__init__(parent)
        self._clearButton = QToolButton(self)
        self._clearButton.setIcon(Toolbox.createIcon('edit-clear'))
        self._clearButton.setCursor(Qt.ArrowCursor)
        self._clearButton.setStyleSheet("QToolButton { border: none; padding: 0; }")
        self._clearButton.hide()
        self._clearButton.clicked.connect(self.clear)
        self.textChanged.connect(self._updateClearButton)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet(QString("QLineEdit { padding-right: %1px; } ").arg(self._clearButton.sizeHint().width() + frameWidth + 1))
        msz = self.minimumSizeHint()
        self.setMinimumSize(max(msz.width(), self._clearButton.sizeHint().height() + frameWidth - 2),
                            max(msz.height(), self._clearButton.sizeHint().height() + frameWidth - 2))
    def resizeEvent(self, event):
        """Takes care of drawing the clear button on the right side."""
        sz = self._clearButton.sizeHint()
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self._clearButton.move(self.rect().right() - frameWidth - sz.width(),
                              (self.rect().bottom() + 2 - sz.height()) / 2)
    def _updateClearButton(self, text):
        """Hide clear button when line edit contains no text."""
        self._clearButton.setVisible(not text.isEmpty())

class RestrictedLineEdit(QLineEdit):
    """Restricted line edit widget.
    An optional prefix can be defined, it is part of the input but can not be
    edited or removed by the user. An optional regular expression prevents
    invalid user input (characters) also a maximum length of the full input
    can be defined.
    """
    def __init__(self, parent = None):
        """Constructur, takes optional reference to parent widget."""
        super(RestrictedLineEdit, self).__init__(parent)
        self._prefix = None
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
            # Make it impossible to remove the prefix.
            self.textChanged.disconnect()
            self.setText(self._prefix)
            self.textChanged.connect(self.validate)

#
# More complex widgets.
#

class EtaCutChart(QWidget):
    """Graphical ETA cut representation."""

    Margin = 10
    Radius = 50
    Length = 100
    FontSize = 7

    def __init__(self, parent = None):
        """Constructur, takes optional reference to parent widget."""
        super(EtaCutChart, self).__init__(parent)
        self.setRange(-5, 5)
        self.setFixedSize(self.Margin * 2 + self.Length, self.Margin * 2 + self.Radius)

    def setRange(self, lower, upper):
        """Set lower and upper bounding of range."""
        self.lower = lower
        self.upper = upper

    def range(self):
        """Returns tuple containing lower and upper bounding of range."""
        return self.lower, self.upper

    def getPoint(self, value):
        """Calculate pixel coordinate for an ETA value."""
        stepX = (self.Length / 2) / 2.5
        stepY = self.Radius / 2.5
        if 2.5 < value <= 5.0:
            return QPoint(self.Margin + self.Length, self.Margin + round(stepY * (value - 2.5)))
        if 0. < value <= 2.5:
            return QPoint(self.Margin + self.Length / 2 + round(stepX * value), self.Margin)
        if -2.5 <= value <= 0.:
            return QPoint(self.Margin + self.Length / 2 + round(stepX * value), self.Margin)
        if -5.0 <= value < -2.5:
            return QPoint(self.Margin, self.Margin + abs(round(stepY * (value + 2.5))))
        raise ValueError()

    def paintEvent(self, event):
        """Paint ETA cut graph on windget."""
        lower, upper = self.range()
        painter = QPainter(self)
        painter.setBrush(Qt.white)
        # Draw Background
        painter.drawRect(self.Margin, self.Margin, self.Length, self.Radius)
        painter.setPen(QPen(Qt.transparent))
        painter.setBrush(Qt.red)
        # Draw Polygon
        polygon = QPolygon()
        polygon.append(QPoint(self.Margin + self.Length / 2, self.Margin + self.Radius))
        polygon.append(self.getPoint(upper))
        if upper > 2.5 and lower < 2.5:
            polygon.append(QPoint(self.Margin + self.Length, self.Margin))
        if lower < -2.5 and upper > -2.5:
            polygon.append(QPoint(self.Margin, self.Margin))
        polygon.append(self.getPoint(lower))
        painter.drawPolygon(polygon)
        # Draw frames
        painter.setPen(QPen(Qt.black))
        painter.setBrush(Qt.transparent)
        painter.drawRect(self.Margin, self.Margin, self.Length / 2, self.Radius)
        painter.drawRect(self.Margin + self.Length / 2, self.Margin, self.Length / 2, self.Radius)
        painter.setFont(QFont('Sans', self.FontSize))
        painter.drawText(QPoint(self.Margin + self.Length / 2 - 2, self.Margin - 1), "0")
        painter.drawText(QPoint(0, (self.Margin + self.Radius) + self.FontSize / 2), u"-5")
        painter.drawText(QPoint(self.Margin + self.Length + 1, (self.Margin + self.Radius) + self.FontSize / 2), u"5")

class PhiCutChart(QWidget):
    """Graphical PHI cut representation."""

    Margin = 8
    Radius = 30
    FontSize = 7

    def __init__(self, parent = None):
        """Constructur, takes optional reference to parent widget."""
        super(PhiCutChart, self).__init__(parent)
        self.setRange(0, 360 * 16)
        self.setFixedSize((self.Margin + self.Radius) * 2, (self.Margin + self.Radius) * 2)

    def setRange(self, lower, upper):
        """Set lower and upper bounding of range."""
        self.lower = lower
        self.upper = upper

    def range(self):
        """Returns tuple containing lower and upper bounding of range."""
        return self.lower, self.upper

    def paintEvent(self, event):
        """Paint PHI cut graph on windget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rectangle = QRect(self.Margin, self.Margin, self.Radius * 2, self.Radius * 2)
        painter.setPen(QPen(Qt.transparent))
        painter.setBrush(Qt.white)
        painter.drawPie(rectangle, 0, 360 * 16)
        painter.setBrush(Qt.red)
        lower, upper = self.range()
        lower = math.degrees(lower)
        upper = math.degrees(upper)
        if (lower < upper):
            painter.drawPie(rectangle, lower * 16, (upper-lower) * 16)
        else:
            painter.drawPie(rectangle, lower * 16, (360 - lower + upper) * 16)
        painter.setPen(QPen(Qt.black))
        painter.setBrush(Qt.transparent)
        painter.drawArc(rectangle, 0, 360 * 16)
        painter.setFont(QFont('Sans', self.FontSize))
        painter.drawText(QPoint(self.Radius * 2 + self.Margin + 2, (self.Margin + self.Radius) + self.FontSize / 2), u"0")
        painter.drawText(QPoint(0, (self.Margin + self.Radius) + self.FontSize / 2), u"π")
