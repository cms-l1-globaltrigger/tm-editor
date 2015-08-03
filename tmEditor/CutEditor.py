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
import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['CutEditorDialog', ]

def suffix(name):
    return "_".join(name.split("_")[1:])

class CutEditorDialog(QDialog):

    CutSettings = Toolbox.readSettings('cuts')

    def __init__(self, menu, parent = None):
        """Param title is the applciation name, version the main applications
        version."""
        super(CutEditorDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Cut Editor"))
        self.menu = menu
        # Cut type
        self.typeLabel = QLabel(self.tr("Type"), self)
        self.typeComboBox = QComboBox(self)
        # Cut suffix
        self.suffixLineEdit = QLineEdit(self)
        self.suffixLabel = QLabel(self.tr("Suffix"), self)
        # Populate cut types.
        for item in self.CutSettings:
            self.typeComboBox.addItem(item['name'])
        #
        self.typeComboBox.currentIndexChanged.connect(self.updateEntries)
        self.minimumLabel = QLabel(self.tr("Minimum"), self)
        self.minimumComboBox = QComboBox(self)#QDoubleSpinBox(self)
        #
        self.maximumLabel = QLabel(self.tr("Maximum"), self)
        self.maximumComboBox = QComboBox(self)#QDoubleSpinBox(self)
        #
        self.dataLabel = QLabel(self.tr("Data"), self)
        self.dataComboBox = QComboBox(self)
        self.infoTextEdit = QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        # Button box
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        # Create layout.
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.typeLabel, 0, 0)
        gridLayout.addWidget(self.typeComboBox, 0, 1)
        gridLayout.addWidget(self.suffixLabel, 1, 0)
        gridLayout.addWidget(self.suffixLineEdit, 1, 1)
        gridLayout.addWidget(self.minimumLabel, 2, 0)
        gridLayout.addWidget(self.minimumComboBox, 2, 1)
        gridLayout.addWidget(self.maximumLabel, 3, 0)
        gridLayout.addWidget(self.maximumComboBox, 3, 1)
        gridLayout.addWidget(self.dataLabel, 4, 0)
        gridLayout.addWidget(self.dataComboBox, 4, 1)
        gridLayout.addWidget(self.infoTextEdit, 0, 2, 5, 1)
        gridLayout.addWidget(buttonBox, 5, 0, 1, 3)
        self.setLayout(gridLayout)
        # Setup connections.
        self.typeComboBox.currentIndexChanged.connect(self.updateEntries)
        # Setup contents.
        self.reset()

    def reset(self):
        self.typeComboBox.setCurrentIndex(0)
        self.suffixLineEdit.setText(self.tr("Unnamed"))
        self.updateEntries()

    def name(self):
        return "{0}_{1}".format(self.typeComboBox.currentText(), self.suffixLineEdit.text())

    def setName(self, name):
        # TODO not nice...
        tokens = name.split('_')
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(tokens[0]))
        self.suffixLineEdit.setText('_'.join(tokens[1:]))

    def object(self):
        """Returns object typ."""
        # TODO not effective, re-write.
        type_ = str(self.typeComboBox.currentText())
        try:
            object, type_ = str(self.typeComboBox.currentText()).split('-')
        except IndexError:
            type_ = str(self.typeComboBox.currentText())
            object = {'MASS': 'mass', 'DR': 'dist', 'DETA': 'dist', 'DPHI': 'dist', 'CHGCOR': 'comb'}[type_]
        return object

    def type(self):
        """Returns cut typ."""
        # TODO not effective, re-write.
        return str(self.typeComboBox.currentText()).split('-')[1]

    def suffix(self):
        """Returns suffix."""
        # TODO not effective, re-write.
        return str(self.suffixLineEdit.text())

    def minimum(self):
        if not self.minimumComboBox.isEnabled():
            return None
        return self.minimumComboBox.itemData(self.minimumComboBox.currentIndex()).toPyObject()['minimum']

    def setMinimum(self, value):
        self.setRangeEnabled(True)
        self.minimumComboBox.setCurrentIndex(self.minimumComboBox.findText(format(float(value), "+.3f")))

    def maximum(self):
        if not self.maximumComboBox.isEnabled():
            return None
        return self.maximumComboBox.itemData(self.maximumComboBox.currentIndex()).toPyObject()['maximum']

    def setMaximum(self, value):
        self.setRangeEnabled(True)
        self.maximumComboBox.setCurrentIndex(self.maximumComboBox.findText(format(float(value), "+.3f")))

    def data(self):
        if not self.dataComboBox.isEnabled():
            return None
        return str(self.dataComboBox.itemData(self.dataComboBox.currentIndex()).toPyObject()) # retuns dict key (lookup index)

    def setData(self, data):
        self.setDataEnabled(True)
        self.dataComboBox.setCurrentIndex(int(data))

    def loadCut(self, cut):
        """Load data from existing cut object, prevents change of type."""
        # TODO not effective, re-write.
        self.typeComboBox.setEnabled(False)
        self.setName(cut.name)
        self.updateEntries()
        if cut.data:
            self.setDataEnabled(True)
            self.setData(cut.data)
        else:
            self.setRangeEnabled(True)
            self.setMinimum(cut.minimum)
            self.setMaximum(cut.maximum)

    def updateCut(self, cut):
        """Update existing cut object with values from editor."""
        # TODO not effective, re-write.
        assert cut.type == self.type()
        assert cut.object == self.object()
        cut['name'] = self.name()
        cut['minimum'] = self.minimum() or ''
        cut['maximum'] = self.maximum() or ''
        cut['data'] = self.data() or ''
        # cut['comment'] = comment

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
        # TODO not effective, re-write.
        name = "{0}-{1}".format(self.object(), self.type())
        item = filter(lambda item: item['name'] == name, self.CutSettings)[0]
        self.infoTextEdit.clear()
        info = []
        if 'title' in item.keys():
            info.append("<p><img src=\":icons/hint.png\"/> <strong>{title}</strong></p>".format(**item))
        if 'description' in item.keys():
            info.append("<p>{description}</p>".format(**item))
        if not self.typeComboBox.isEnabled():
            info.append("<p><strong>Note:</strong> Changing an existing cut's type is not allowed.</p>".format(**item))
        self.infoTextEdit.setText("".join(info))
        if 'data' in item.keys():
            self.setDataEnabled(True)
            self.minimumComboBox.clear()
            self.maximumComboBox.clear()
            self.dataComboBox.clear()
            # brrrr.... >_<'
            for key in [str(i) for i in sorted([int(key) for key in item['data'].keys()])]:
                self.dataComboBox.addItem(item['data'][key], key)
        else:
            self.setRangeEnabled(True)
            scale = self.menu.scales.bins[name]
            self.minimumComboBox.clear()
            for entry in scale:
                self.minimumComboBox.addItem(format(float(entry['minimum']), "+.3f"), entry)

            self.maximumComboBox.clear()
            for entry in scale:
                self.maximumComboBox.addItem(format(float(entry['maximum']), "+.3f"), entry)
            self.maximumComboBox.setCurrentIndex(self.maximumComboBox.count() - 1)

            self.dataComboBox.clear()
