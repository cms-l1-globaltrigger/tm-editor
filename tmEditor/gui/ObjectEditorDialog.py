#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import tmGrammar

from tmEditor.core import Toolbox

from tmEditor.core.Types import ThresholdObjectTypes
from tmEditor.core.Types import CountObjectTypes
from tmEditor.core.Types import ObjectCutTypes

from tmEditor.core.Algorithm import toObject, objectCuts
from tmEditor.core.AlgorithmHelper import AlgorithmHelper, decode_threshold
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter

# Common widgets
from tmEditor.gui.CommonWidgets import PrefixedSpinBox
from tmEditor.gui.CommonWidgets import TextFilterWidget
from tmEditor.gui.CommonWidgets import ComboBoxPlus

from PyQt4 import QtCore
from PyQt4 import QtGui

import sys, os
import re

__all__ = ['ObjectEditorDialog', ]

# -----------------------------------------------------------------------------
#  Keys
# -----------------------------------------------------------------------------

kMinimum = 'minimum'
kMaximum = 'maximum'
kObject = 'object'
kStep = 'step'
kType = 'type'
kET = 'ET'
kCOUNT = 'COUNT'

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def cutItem(text, checked=False):
    """Retruns a checkable cut standard item, to be inserted to a list model."""
    item = QtGui.QStandardItem(text)
    item.setEditable(False)
    item.setCheckable(True)
    if checked:
        item.setCheckState(QtCore.Qt.Checked)
    return item

# -----------------------------------------------------------------------------
#  Object editor dialog class
# -----------------------------------------------------------------------------

class ObjectEditorDialog(QtGui.QDialog):
    """Object editor dialog class."""

    def __init__(self, menu, parent=None):
        """Constructor, takes a reference to a menu and an optional parent."""
        super(ObjectEditorDialog, self).__init__(parent)
        self.menu = menu
        self.setupUi()
        self.initObjectList(menu)
        self.initCuts()
        self.updateObjectType()
        # Connect signals
        self.typeComboBox.currentIndexChanged.connect(self.updateObjectType)
        self.compareComboBox.currentIndexChanged.connect(self.updateInfoText)
        self.thresholdSpinBox.valueChanged.connect(self.updateInfoText)
        self.offsetSpinBox.valueChanged.connect(self.updateInfoText)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.updateInfoText()

    def setupUi(self):
        self.setWindowIcon(Toolbox.createIcon("wizard"))
        self.setWindowTitle(self.tr("Object Requirement Editor"))
        self.resize(640, 380)
        self.objectLabel = QtGui.QLabel(self.tr("Object"), self)
        self.objectLabel.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        self.typeComboBox = ComboBoxPlus(self)
        self.typeComboBox.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        self.compareComboBox = QtGui.QComboBox(self)
        self.compareComboBox.addItem('=>', tmGrammar.GE)
        self.compareComboBox.addItem('==', tmGrammar.EQ)
        self.thresholdSpinBox = QtGui.QDoubleSpinBox(self)
        self.offsetSpinBox = PrefixedSpinBox(self)
        self.offsetSpinBox.setRange(-2, 2)
        self.offsetSpinBox.setValue(0)
        self.offsetSpinBox.setSuffix(self.tr(" BX"))
        self.cutLabel = QtGui.QLabel(self.tr("Cuts"), self)
        self.cutLabel.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        self.cutListView = QtGui.QListView(self)
        self.cutListView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.cutListView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.filterWidget = TextFilterWidget(self)
        self.infoTextEdit = QtGui.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        layout = QtGui.QGridLayout()
        layout.addWidget(self.objectLabel, 0, 0)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.typeComboBox)
        hbox.addWidget(self.compareComboBox)
        hbox.addWidget(self.thresholdSpinBox)
        hbox.addWidget(self.offsetSpinBox)
        layout.addLayout(hbox, 0, 1)
        layout.addWidget(self.cutLabel, 1, 0)
        layout.addWidget(self.cutListView, 1, 1)
        layout.addWidget(self.filterWidget, 2, 1)
        layout.addWidget(self.infoTextEdit, 0, 2, 3, 1)
        layout.addWidget(self.buttonBox, 3, 0, 1, 3)
        self.setLayout(layout)

    def updateObjectType(self):
        objectType = self.objectType()
        if objectType in ThresholdObjectTypes:
            self.thresholdSpinBox.setSuffix(" GeV")
            self.thresholdSpinBox.setDecimals(1)
        elif objectType in CountObjectTypes:
            self.thresholdSpinBox.setDecimals(0)
            self.thresholdSpinBox.setSuffix("")
        scale = self.getScale(objectType)
        # Just to make sure...
        if scale is None:
            QtGui.QMessageBox.critical(self,
                self.tr("Failed to load scales"),
                QtCore.QString("Missing scales for object of type %1").arg(objectType),
            )
            return
        self.thresholdSpinBox.setRange(float(scale[kMinimum]), float(scale[kMaximum]))
        self.thresholdSpinBox.setSingleStep(float(scale[kStep]))
        self.updateInfoText()
        self.initCuts()

    def initObjectList(self, menu):
        """Initialize list of available objects. Ignores objects with no scales."""
        for index, name in enumerate(ThresholdObjectTypes + CountObjectTypes):
            self.typeComboBox.addItem(Toolbox.miniIcon(name.lower()), name)
            if not self.getScale(name): # on missing scale (editing outdated XML?)
                self.typeComboBox.setItemEnabled(index, False)

    def initCuts(self):
        """Initialize list of checkable cuts."""
        self.cutModel = QtGui.QStandardItemModel(self)
        self.cutModel._items = []
        for cut in sorted(self.menu.cuts, key=lambda cut: cut.name):
            if cut.object == self.objectType():
                item = cutItem(cut.name)
                self.cutModel.appendRow(item)
                self.cutModel._items.append(item)
        self.cutProxy = QtGui.QSortFilterProxyModel(self)
        self.cutProxy.setFilterKeyColumn(-1) # Filter all collumns
        self.cutProxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.cutProxy.setSourceModel(self.cutModel)
        self.cutModel.itemChanged.connect(self.updateInfoText)
        self.cutListView.setModel(self.cutProxy)
        self.filterWidget.textChanged.connect(self.updateFilter)

    def getScale(self, objectType):
        """Returns scale for object or None if not found."""
        # Get only scales of object type
        scales = filter(lambda item: item[kObject] == objectType, self.menu.scales.scales)
        # Get only threshold/count scales
        return (filter(lambda item: item[kType] in (kET, kCOUNT, ), scales) or [None])[0]

    def updateFilter(self, text):
        """Update cut filter."""
        self.cutListView.model().setFilterWildcard(text)

    def objectType(self):
        """Returns object type."""
        return str(self.typeComboBox.currentText())

    def comparisonOperator(self):
        """Returns comparison operator."""
        return str(self.compareComboBox.itemData(self.compareComboBox.currentIndex()).toPyObject())

    def threshold(self):
        """Returns objects threshold."""
        return self.thresholdSpinBox.value()

    def bxOffset(self):
        return self.offsetSpinBox.value()

    def selectedCuts(self):
        """Retruns list of checked cut names."""
        return [str(item.text()) for item in filter(lambda item: item.checkState() == QtCore.Qt.Checked, self.cutModel._items)]

    def expression(self):
        """Returns object expression selected by the inputs."""
        expression = AlgorithmHelper()
        expression.addObject(
            type = self.objectType(),
            comparison_operator = self.comparisonOperator(),
            threshold = self.threshold(),
            bx_offset = self.bxOffset(),
            cuts = self.selectedCuts(),
        )
        return AlgorithmFormatter.normalize(expression.serialize())

    def updateInfoText(self):
        """Update info box text."""
        objectType = self.objectType()
        scale = self.getScale(objectType)
        minThreshold = float(scale[kMinimum])
        maxThreshold = float(scale[kMaximum])
        step = float(scale[kStep])
        expression = self.expression()
        text = []
        text.append('<h3>{objectType} Object Requirement</h3>')
        if objectType in ThresholdObjectTypes:
            text.append('<p>Valid threshold: {minThreshold:.1f} GeV - {maxThreshold:.1f} GeV ({step:.1f} GeV steps)</p>')
        elif objectType in CountObjectTypes:
            text.append('<p>Valid count: {minThreshold:.0f} - {maxThreshold:.0f}</p>')
        text.append('<h4>Preview</h4>')
        text.append('<p><pre>{expression}</pre></p>')
        self.infoTextEdit.setText(''.join(text).format(**locals()))

    def loadObject(self, token):
        """Load dialog by values from object. Will raise a ValueError if string
        *token* is not a valid object.
        """
        object = toObject(token)
        object.cuts = objectCuts(token)
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(object.type))
        self.compareComboBox.setCurrentIndex(self.compareComboBox.findData(object.comparison_operator))
        self.thresholdSpinBox.setValue(object.decodeThreshold())
        self.offsetSpinBox.setValue(object.bx_offset)
        for cut in self.cutModel._items:
            if cut.text() in object.cuts:
                cut.setCheckState(QtCore.Qt.Checked)

# -----------------------------------------------------------------------------
#  Unit test
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from tmEditor import Menu
    app = QtGui.QApplication(sys.argv)
    menu = Menu(sys.argv[1])
    window = ObjectEditor(menu)
    window.show()
    sys.exit(app.exec_())
