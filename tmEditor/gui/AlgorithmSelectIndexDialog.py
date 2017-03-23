# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm select index dialog.

class AlgorithmSelectIndexDialog
"""

import tmGrammar

from tmEditor.core import toolbox
from tmEditor.core.Settings import MaxAlgorithms

# Common widgets
from tmEditor.gui.CommonWidgets import IconLabel, createIcon

from tmEditor.PyQt5Proxy import QtCore
from tmEditor.PyQt5Proxy import QtWidgets
from tmEditor.PyQt5Proxy import pyqt4_str

import sys, os

__all__ = ['AlgorithmSelectIndexDialog', ]

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def map_reserved(reserved):
    """Returns state map for all buttons."""
    return [index in reserved for index in range(MaxAlgorithms)]

def map_free(free):
    """Returns state map for all buttons."""
    return [index not in free for index in range(MaxAlgorithms)]

def find_gaps(reserved, size=1):
    """Retruns list of free indices ranges to accomodate chunks of *size*."""
    states = map_reserved(reserved)
    gaps = set()
    index = 0
    while index < MaxAlgorithms:
        try:
            next_free = states.index(False, index)
        except ValueError:
            break
        try:
            next_reserved = states.index(True, next_free)
        except ValueError:
            next_reserved = MaxAlgorithms
        gap_min = next_free
        gap_max = next_reserved - 1
        gap_size = gap_max - gap_min + 1
        if size <= gap_size:
            gaps.update(range(gap_min, (gap_max + 1)-size + 1)) # remove offset by bunch size
        index = next_reserved
    return list(gaps)

# -----------------------------------------------------------------------------
#  Algorithm select index dialog.
# -----------------------------------------------------------------------------

class AlgorithmSelectIndexDialog(QtWidgets.QDialog):
    """Dialog for graphical selection of algorithm index.
    Displays a button grid representing all available index slots.
    Already used indices are disabled, free indices are enabled. User can assign
    an index by clicking a free index button.
    """
    # Define size of the index grid.
    ColumnCount = 8
    RowCount    = MaxAlgorithms // ColumnCount

    def __init__(self, parent=None):
        super(AlgorithmSelectIndexDialog, self).__init__(parent)
        # Setup window
        self.setWindowTitle(self.tr("Select Index"))
        self.resize(480, 300)
        # Button box with cancel button
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setAutoDefault(False)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        # Layout to add Buttons
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.setHorizontalSpacing(2)
        gridLayout.setVerticalSpacing(2)
        self.gridWidget = QtWidgets.QWidget(self)
        # Variable to iterate over all indices.
        index = 0
        # Add items to the grid in the scroll area
        self.buttons = []
        for row in range(self.RowCount):
            for column in range(self.ColumnCount):
                if index >= MaxAlgorithms:
                    break
                button = QtWidgets.QPushButton(format(index), self)
                button.index = index
                button.setCheckable(True)
                button.setMaximumWidth(50)
                button.clicked[bool].connect(self._updateIndex)
                self.buttons.append(button)
                gridLayout.addWidget(button, row, column)
                # Increment index.
                index += 1
        # Create a scroll area for the preview
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        # Layout for Dailog Window
        self.gridWidget.setLayout(gridLayout)
        self.scrollArea.setWidget(self.gridWidget)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.scrollArea)
        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addWidget(IconLabel(createIcon("info"), self.tr("Select a free algorithm index."), self))
        bottomLayout.addWidget(self.buttonBox)
        layout.addLayout(bottomLayout)
        self.setLayout(layout)

    def setup(self, index, reserved):
        """Setup button states, disable reserved indices."""
        for button in self.buttons:
            if button.index in reserved:
                button.setChecked(True)
                button.setEnabled(False)
            if button.index == index:
                button.setChecked(True)
                button.setEnabled(True)
                self.currentButton = button
        self.scrollArea.ensureWidgetVisible(self.currentButton)

    def _updateIndex(self):
        """Get new index from the button."""
        self.index = self.sender().index
        self.accept()

# -----------------------------------------------------------------------------
#  Unit test
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    bundle_size = 3

    reserved = [0,2,3,4,5,16,17,18,26,46,47,49,50,51,101,510,511]
    gaps = find_gaps(reserved, bundle_size)

    window = AlgorithmSelectIndexDialog()
    window.setup(42, reserved)
    window.show()
    sys.exit(app.exec_())
