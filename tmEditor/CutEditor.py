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

    CutSettings = Toolbox.readSettings('cuts')

    def __init__(self, menu, parent = None):
        """Param title is the applciation name, version the main applications
        version."""
        super(CutEditorDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Cut Editor"))
        self.menu = menu
        #
        self.suffixLineEdit = QLineEdit(self)
        self.typeComboBox = QComboBox(self)
        for item in self.CutSettings:
            self.typeComboBox.addItem(item['name'])
        self.typeComboBox.currentIndexChanged.connect(self.updateEntries)
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
        gridLayout.addWidget(QLabel("Type", self), 0, 0)
        gridLayout.addWidget(self.typeComboBox, 0, 1)
        gridLayout.addWidget(QLabel("Suffix", self), 1, 0)
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
        return "{0}_{1}".format(self.typeComboBox.currentText(), self.suffixLineEdit.text())

    def setName(self, name):
        tokens = name.split('_')
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(tokens[0]))
        self.suffixLineEdit.setText('_'.join(tokens[1:]))

    def type(self):
        """Returns cut typ."""
        return str(self.typeComboBox.currentText())

    def minimum(self):
        return self.minimumComboBox.itemData(self.minimumComboBox.currentIndex()).toPyObject()['minimum']

    def setMinimum(self, value):
        self.minimumComboBox.setCurrentIndex(self.minimumComboBox.findText(format(float(value), "+.3f")))

    def maximum(self):
        return self.maximumComboBox.itemData(self.maximumComboBox.currentIndex()).toPyObject()['maximum']

    def setMaximum(self, value):
        self.maximumComboBox.setCurrentIndex(self.maximumComboBox.findText(format(float(value), "+.3f")))

    def data(self):
        if not self.dataComboBox.isEnabled():
            return None
        return self.dataComboBox.itemData(self.dataComboBox.currentIndex()).toPyObject() # retuns dict key (lookup index)

    def setData(self, data):
        pass

    def loadCut(self, cut):
        """Load data from existing cut object, prevents change of type."""
        self.typeComboBox.setEnabled(False)

    def updateCut(self, cut):
        """Update existing cut object with values from editor."""
        assert cut.type == self.type()

    def setRangeEnabled(self, enabled):
        """Set range inputs enabled, diables data input."""
        self.minimumLabel.setEnabled(enabled)
        self.minimumComboBox.setEnabled(enabled)
        self.maximumLabel.setEnabled(enabled)
        self.maximumComboBox.setEnabled(enabled)
        self.dataLabel.setEnabled(not enabled)
        self.dataComboBox.setEnabled(not enabled)

    def setDataEnabled(self, enabled):
        """Set data input enabled, diables range inputs."""
        self.setRangeEnabled(not enabled)

    def updateEntries(self):
        name = str(self.typeComboBox.currentText())
        item = filter(lambda item: item['name'] == name, self.CutSettings)[0]
        if 'data' in item.keys():
            self.setDataEnabled(True)
            self.minimumComboBox.clear()
            self.maximumComboBox.clear()
            self.dataComboBox.clear()
            for key, value in item['data'].items():
                self.dataComboBox.addItem(value, key)
        else:
            self.setRangeEnabled(True)
            print list(self.menu.scales.bins.keys())
            print
            scale = self.menu.scales.bins[name]
            self.minimumComboBox.clear()
            for entry in scale:
                self.minimumComboBox.addItem(format(float(entry['minimum']), "+.3f"), entry)

            self.maximumComboBox.clear()
            for entry in scale:
                self.maximumComboBox.addItem(format(float(entry['maximum']), "+.3f"), entry)
            self.maximumComboBox.setCurrentIndex(self.maximumComboBox.count() - 1)

            self.dataComboBox.clear()
