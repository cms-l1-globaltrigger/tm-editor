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
        dict(name = 'MU-ETA', title = "Muon eta"),
        dict(name = 'MU-PHI', title = "Muon phi"),
        dict(name = 'MU-QLTY', title = "Muon quality"),
        dict(name = 'MU-ISO', title = "Muon isolation", data = genericRangeDict(2**2)),
        dict(name = 'MU-CHG', title = "Muon charge", data = genericRangeDict(4**2)),
        dict(name = 'EG-ETA', title = "Electron/gamma eta"),
        dict(name = 'EG-PHI', title = "Electron/gamma phi"),
        dict(name = 'EG-QLTY', title = "Electron/gamma quality", data = genericRangeDict(4**2)),
        dict(name = 'EG-ISO', title = "Electron/gamma isolation", data = genericRangeDict(2**2)),
        dict(name = 'JET-ETA', title = "Jet eta"),
        dict(name = 'JET-PHI', title = "Jet phi"),
        dict(name = 'JET-QLTY', title = "Jet quality"),
        dict(name = 'TAU-ETA', title = "Tau eta"),
        dict(name = 'TAU-PHI', title = "Tau phi"),
        dict(name = 'TAU-QLTY', title = "Tau quality", data = genericRangeDict(4**2)),
        dict(name = 'TAU-ISO', title = "Tau isolation", data = genericRangeDict(2**2)),
        dict(name = 'ETM-PHI', title = "Missing energy phi"),
        dict(name = 'HTM-PHI', title = "Missing ? phi"),
        dict(name = 'CHGCOR', title = "Charge correlation",
            data = {
                0: "same sign",
                1: "opposite sign",
            }
        ),
        dict(name = 'DETA', title = "Delta eta"),
        dict(name = 'DPHI', title = "Delta phi"),
        dict(name = 'DR', title = "Delta-R"),
        dict(name = 'MASS', title = "Invariant mass"),
    )

    def __init__(self, menu, parent = None):
        """Param title is the applciation name, version the main applications
        version."""
        super(CutEditorDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Cut Editor"))
        self.menu = menu
        #
        self.suffixLineEdit = QLineEdit(self)
        self.objectComboBox = QComboBox(self)
        for item in self.CutItems:
            self.objectComboBox.addItem(item['name'])
        self.objectComboBox.currentIndexChanged.connect(self.updateEntries)
        self.minimumComboBox = QComboBox(self)#QDoubleSpinBox(self)
        # self.minimumComboBox.setDecimals(3)
        self.maximumComboBox = QComboBox(self)#QDoubleSpinBox(self)
        # self.maximumComboBox.setDecimals(3)
        self.dataComboBox = QComboBox(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.minimumLabel = QLabel("Minimum", self)
        self.maximumLabel = QLabel("Maximum", self)
        self.dataLabel = QLabel("Data", self)
        #
        gridLayout = QGridLayout()
        gridLayout.addWidget(QLabel("Object", self), 0, 0)
        gridLayout.addWidget(self.objectComboBox, 0, 1)
        gridLayout.addWidget(QLabel("Name", self), 1, 0)
        gridLayout.addWidget(self.suffixLineEdit, 1, 1)
        gridLayout.addWidget(self.minimumLabel, 2, 0)
        gridLayout.addWidget(self.minimumComboBox, 2, 1)
        gridLayout.addWidget(self.maximumLabel, 3, 0)
        gridLayout.addWidget(self.maximumComboBox, 3, 1)
        gridLayout.addWidget(self.dataLabel, 4, 0)
        gridLayout.addWidget(self.dataComboBox, 4, 1)
        gridLayout.addWidget(buttonBox, 5, 0, 5, 2)
        self.setLayout(gridLayout)

    def name(self):
        return "{0}_{1}".format(self.objectComboBox.currentText(), self.suffixLineEdit.text())

    def setName(self, name):
        tokens = name.split('_')
        self.objectComboBox.setCurrentIndex(self.objectComboBox.findText(tokens[0]))
        self.suffixLineEdit.setText('_'.join(tokens[1:]))

    def minimum(self):
        return self.minimumComboBox.itemData(self.minimumComboBox.currentIndex())['minimum']

    def setMinimum(self, value):
        self.minimumComboBox.setCurrentIndex(self.minimumComboBox.findText(format(value, "+.3f")))

    def maximum(self):
        return self.maximumComboBox.itemData(self.maximumComboBox.currentIndex())['maximum']

    def setMaximum(self, value):
        self.maximumComboBox.setCurrentIndex(self.maximumComboBox.findText(format(value, "+.3f")))

    def data(self):
        if not self.dataComboBox.isEnabled():
            return None
        return self.dataComboBox.itemData(self.dataComboBox.currentIndex()) # retuns dict key (lookup index)

    def updateEntries(self):
        name = str(self.objectComboBox.currentText())
        item = filter(lambda item: item['name'] == name, self.CutItems)[0]
        if 'data' in item.keys():
            self.minimumLabel.setEnabled(False)
            self.minimumComboBox.setEnabled(False)
            self.minimumComboBox.clear()
            self.maximumLabel.setEnabled(False)
            self.maximumComboBox.setEnabled(False)
            self.maximumComboBox.clear()
            self.dataComboBox.setEnabled(True)
            self.dataLabel.setEnabled(True)
            self.dataComboBox.clear()
            for key, value in item['data'].items():
                self.dataComboBox.addItem(value, key)
        else:
            scale = self.menu.scales.bins[name]
            self.minimumLabel.setEnabled(True)
            self.minimumComboBox.setEnabled(True)
            self.minimumComboBox.clear()
            for entry in scale:
                self.minimumComboBox.addItem(format(float(entry['minimum']), "+.3f"), entry)

            self.maximumLabel.setEnabled(True)
            self.maximumComboBox.setEnabled(True)
            self.maximumComboBox.clear()
            for entry in scale:
                self.maximumComboBox.addItem(format(float(entry['maximum']), "+.3f"), entry)
            self.maximumComboBox.setCurrentIndex(self.maximumComboBox.count() - 1)

            self.dataComboBox.setEnabled(False)
            self.dataLabel.setEnabled(False)
            self.dataComboBox.clear()
