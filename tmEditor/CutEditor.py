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
import tmGrammar
from collections import namedtuple

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['CutEditorDialog', ]

def genericRangeDict(count):
    return dict([(i, format(i, "04X")) for i in range(count)])

class CutEditorDialog(QDialog):

    #
    # TODO: read this from YAML side file?!
    # If no data key defined lookup the scales set and fetch lookup table.
    #
    CutItems = (
        dict(name = 'MU-ETA', title = ""),
        dict(name = 'MU-PHI', title = ""),
        dict(name = 'MU-QLTY', title = ""),
        dict(name = 'MU-ISO', title = "", data = genericRangeDict(2**2)),
        dict(name = 'MU-CHG', title = "", data = genericRangeDict(4**2)),
        dict(name = 'EG-ETA', title = ""),
        dict(name = 'EG-PHI', title = ""),
        dict(name = 'EG-QLTY', title = "", data = genericRangeDict(4**2)),
        dict(name = 'EG-ISO', title = "", data = genericRangeDict(2**2)),
        dict(name = 'JET-ETA', title = ""),
        dict(name = 'JET-PHI', title = ""),
        dict(name = 'JET-QLTY', title = ""),
        dict(name = 'TAU-ETA', title = ""),
        dict(name = 'TAU-QLTY', title = "", data = genericRangeDict(4**2)),
        dict(name = 'TAU-ISO', title = "", data = genericRangeDict(2**2)),
        dict(name = 'TAU-PHI', title = ""),
        dict(name = 'ETM-PHI', title = ""),
        dict(name = 'HTM-PHI', title = ""),
        dict(name = 'CHGCOR', title = "Charge correlation",
            data = {
                0: "same sign",
                1: "opposite sign",
            }
        ),
        dict(name = 'DETA', title = ""),
        dict(name = 'DPHI', title = ""),
        dict(name = 'DR', title = ""),
        dict(name = 'MASS', title = ""),
    )

    def __init__(self, menu, parent = None):
        """Param title is the applciation name, version the main applications
        version."""
        super(CutEditorDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Cut Editor"))
        self.menu = menu
        #
        self.nameLineEdit = QLineEdit(self)
        self.objectComboBox = QComboBox(self)
        for name in tmGrammar.cutName:
            self.objectComboBox.addItem(name)
        self.objectComboBox.currentIndexChanged.connect(self.updateEntries)
        self.minimumSpinBox = QComboBox(self)#QDoubleSpinBox(self)
        # self.minimumSpinBox.setDecimals(3)
        self.maximumSpinBox = QComboBox(self)#QDoubleSpinBox(self)
        # self.maximumSpinBox.setDecimals(3)
        self.dataComboBox = QComboBox(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.minimumLabel = QLabel("Minimum", self)
        self.maximumLabel = QLabel("Maximum", self)
        self.dataLabel = QLabel("Data", self)
        #
        gridLayout = QGridLayout()
        gridLayout.addWidget(QLabel("Name", self), 0, 0)
        gridLayout.addWidget(self.nameLineEdit, 0, 1)
        gridLayout.addWidget(QLabel("Object", self), 1, 0)
        gridLayout.addWidget(self.objectComboBox, 1, 1)
        gridLayout.addWidget(self.minimumLabel, 3, 0)
        gridLayout.addWidget(self.minimumSpinBox, 3, 1)
        gridLayout.addWidget(self.maximumLabel, 4, 0)
        gridLayout.addWidget(self.maximumSpinBox, 4, 1)
        gridLayout.addWidget(self.dataLabel, 5, 0)
        gridLayout.addWidget(self.dataComboBox, 5, 1)
        gridLayout.addWidget(buttonBox, 6, 0, 6, 2)
        self.setLayout(gridLayout)

    def name(self):
        return str(self.nameLineEdit.text())

    def setName(self, name):
        self.nameLineEdit.setText(name)

    def updateEntries(self):
        name = str(self.objectComboBox.currentText())
        item = filter(lambda item: item['name'] == name, self.CutItems)[0]
        if 'data' in item.keys():
            self.minimumLabel.setEnabled(False)
            self.minimumSpinBox.setEnabled(False)
            self.minimumSpinBox.clear()
            self.maximumLabel.setEnabled(False)
            self.maximumSpinBox.setEnabled(False)
            self.maximumSpinBox.clear()
            self.dataComboBox.setEnabled(True)
            self.dataLabel.setEnabled(True)
            self.dataComboBox.clear()
            for key, value in item['data'].items():
                self.dataComboBox.addItem(value, key)
        else:
            scale = self.menu.scales.bins[name]
            self.minimumLabel.setEnabled(True)
            self.minimumSpinBox.setEnabled(True)
            self.minimumSpinBox.clear()
            for entry in scale:
                self.minimumSpinBox.addItem(format(float(entry['minimum']), "+.3f"), entry)

            self.maximumLabel.setEnabled(True)
            self.maximumSpinBox.setEnabled(True)
            self.maximumSpinBox.clear()
            for entry in scale:
                self.maximumSpinBox.addItem(format(float(entry['maximum']), "+.3f"), entry)
            self.maximumSpinBox.setCurrentIndex(self.maximumSpinBox.count() - 1)

            self.dataComboBox.setEnabled(False)
            self.dataLabel.setEnabled(False)
            self.dataComboBox.clear()
