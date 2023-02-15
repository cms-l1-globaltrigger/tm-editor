"""Algorithm select index dialog.

class AlgorithmSelectIndexDialog
"""

from PyQt5 import QtCore, QtWidgets

from tmEditor.core.Settings import MaxAlgorithms

# Common widgets
from tmEditor.gui.CommonWidgets import IconLabel, createIcon

__all__ = ['AlgorithmSelectIndexDialog', ]

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def map_expand(indices):
    return [index in indices for index in range(MaxAlgorithms)]

def match_pattern(a, b):
    assert len(a) == len(b)
    for i in range(len(a)):
        if a[i] and b[i]:
            return False
    return True

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
    RowCount = MaxAlgorithms // ColumnCount

    def __init__(self, parent=None):
        super().__init__(parent)
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
                #self._setButtonStyle(button, self.Green)
                button.clicked.connect(self._updateIndex)
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

    def setup(self, occupied, selected):
        """Setup button states, disable reserved indices."""

        occupied = list(set(occupied)-set(selected))
        occupied_pattern = map_expand(occupied)
        selected_pattern = map_expand(selected)[selected[0]:selected[-1]+1]
        free = []
        for i in range(MaxAlgorithms):
            a = occupied_pattern[i:i+len(selected_pattern)]
            b = selected_pattern
            if len(a) == len(b):
                if match_pattern(a, b):
                    free.append(i)

        self.mapping = {}
        self.selected = selected

        for button in self.buttons:
            button.setChecked(False)
            button.setEnabled(False)
            button.setStyleSheet("font-weight: normal; color: grey;")
            if button.index in free:
                button.setEnabled(True)
                button.setStyleSheet("font-weight: normal; color: green;")
            if button.index in occupied:
                button.setChecked(True)
                button.setEnabled(False)
                button.setStyleSheet("font-weight: normal; color: red;")
            if button.index in selected:
                self.mapping[button.index] = button.index
                button.setChecked(True)
                #button.setEnabled(True)
                button.setStyleSheet("font-weight: bold; color: blue;")
                self.currentButton = button
                self.scrollArea.ensureWidgetVisible(self.currentButton)

    def _updateIndex(self):
        """Get new index from the button."""
        diff = self.selected[0] - self.sender().index
        self.index = self.sender().index
        for k, v in self.mapping.items():
            if diff > 0:
                self.mapping[k] = v - abs(diff)
            else:
                self.mapping[k] = v + abs(diff)
        self.accept()
