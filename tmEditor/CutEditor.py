# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Cut editor dialog.
"""

from tmEditor import (
    Toolbox,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['CutEditorDialog', ]

class CutEditorDialog(QDialog):

    def __init__(self, menu, parent = None):
        """Param title is the applciation name, version the main applications
        version."""
        super(CutEditorDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Cut Editor"))
        self.menu = menu
        #
        self.nameLineEdit = QLineEdit(self)
        self.objectComboBox = QComboBox(self)
        self.objectComboBox.addItem("MU")
        self.objectComboBox.addItem("EG")
        self.objectComboBox.addItem("TAU")
        self.objectComboBox.addItem("JET")
        self.typeComboBox = QComboBox(self)
        self.typeComboBox.addItem("ETA")
        self.typeComboBox.addItem("PHI")
        self.minimumSpinBox = QDoubleSpinBox(self)
        self.minimumSpinBox.setDecimals(3)
        self.maximumSpinBox = QDoubleSpinBox(self)
        self.maximumSpinBox.setDecimals(3)
        self.dataComboBox = QComboBox(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        #
        gridLayout = QGridLayout()
        gridLayout.addWidget(QLabel("Name", self), 0, 0)
        gridLayout.addWidget(self.nameLineEdit, 0, 1)
        gridLayout.addWidget(QLabel("Object", self), 1, 0)
        gridLayout.addWidget(self.objectComboBox, 1, 1)
        gridLayout.addWidget(QLabel("Type", self), 2, 0)
        gridLayout.addWidget(self.typeComboBox, 2, 1)
        gridLayout.addWidget(QLabel("Minimum", self), 3, 0)
        gridLayout.addWidget(self.minimumSpinBox, 3, 1)
        gridLayout.addWidget(QLabel("Maximum", self), 4, 0)
        gridLayout.addWidget(self.maximumSpinBox, 4, 1)
        gridLayout.addWidget(QLabel("Data", self), 5, 0)
        gridLayout.addWidget(self.dataComboBox, 5, 1)
        gridLayout.addWidget(buttonBox, 6, 0, 6, 2)
        self.setLayout(gridLayout)

    def name(self):
        return str(self.nameLineEdit.text())

    def setName(self, name):
        self.nameLineEdit.setText(name)
