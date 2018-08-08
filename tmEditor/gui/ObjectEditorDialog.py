#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import tmGrammar

from tmEditor.core.Settings import CutSpecs
from tmEditor.core.formatter import fCutLabel
from tmEditor.core.types import ThresholdObjectTypes
from tmEditor.core.types import CountObjectTypes
from tmEditor.core.types import ObjectCutTypes
from tmEditor.core.types import ObjectTypes

from tmEditor.core.Algorithm import toObject, objectCuts
from tmEditor.core.AlgorithmHelper import AlgorithmHelper, decode_threshold
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter

# Common widgets
from tmEditor.gui.CommonWidgets import PrefixedSpinBox
from tmEditor.gui.CommonWidgets import TextFilterWidget
from tmEditor.gui.CommonWidgets import ComboBoxPlus
from tmEditor.gui.CommonWidgets import createIcon, miniIcon

from tmEditor.gui.CutEditorDialog import CutEditorDialog

from tmEditor.PyQt5Proxy import QtCore
from tmEditor.PyQt5Proxy import QtGui
from tmEditor.PyQt5Proxy import QtWidgets
from tmEditor.PyQt5Proxy import pyqt4_toPyObject, pyqt4_str

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
#  Cut item class
# -----------------------------------------------------------------------------

class CutItem(QtGui.QStandardItem):
    """A checkable cut standard item, to be inserted to a list model."""

    def __init__(self, text, checked=False):
        super(CutItem, self).__init__(text)
        self.setEditable(False)
        self.setCheckable(True)
        if checked:
            self.setCheckState(QtCore.Qt.Checked)

# -----------------------------------------------------------------------------
#  Object editor dialog class
# -----------------------------------------------------------------------------

class ObjectEditorDialog(QtWidgets.QDialog):
    """Object editor dialog class."""

    def __init__(self, menu, parent=None, objects=None):
        """Constructor, takes a reference to a menu and an optional parent.
        Optionally a custom list of objects can be assigned to the dialog.
        """
        super(ObjectEditorDialog, self).__init__(parent)
        self.menu = menu
        self.setupUi()
        self.objectTypes = objects or ObjectTypes
        self.initObjectList(self.objectTypes)
        self.initCuts()
        self.updateObjectType()
        # Connect signals
        self.typeComboBox.currentIndexChanged.connect(self.updateObjectType)
        self.compareComboBox.currentIndexChanged.connect(self.updateInfoText)
        self.thresholdSpinBox.valueChanged.connect(self.updateInfoText)
        self.offsetSpinBox.valueChanged.connect(self.updateInfoText)
        self.addCutButton.clicked.connect(self.addCut)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # Initialize
        self.updateInfoText()

    def setupUi(self):
        self.setWindowIcon(createIcon("wizard-object"))
        self.setWindowTitle(self.tr("Object Requirement Editor"))
        self.resize(640, 380)
        self.objectLabel = QtWidgets.QLabel(self.tr("Object"), self)
        self.objectLabel.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        self.typeComboBox = ComboBoxPlus(self)
        self.typeComboBox.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        self.compareComboBox = QtWidgets.QComboBox(self)
        self.compareComboBox.addItem('>=', tmGrammar.GE)
        self.compareComboBox.addItem('==', tmGrammar.EQ)
        self.thresholdSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.offsetSpinBox = PrefixedSpinBox(self)
        self.offsetSpinBox.setRange(-2, 2)
        self.offsetSpinBox.setValue(0)
        self.offsetSpinBox.setSuffix(self.tr(" BX"))
        self.cutLabel = QtWidgets.QLabel(self.tr("Cuts"), self)
        self.cutLabel.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        self.cutListView = QtWidgets.QListView(self)
        self.cutListView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.cutListView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.filterWidget = TextFilterWidget(self)
        self.addCutButton = QtWidgets.QPushButton(createIcon("list-add"), self.tr("Add..."), self)
        self.infoTextEdit = QtWidgets.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.objectLabel, 0, 0)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.typeComboBox)
        hbox.addWidget(self.compareComboBox)
        hbox.addWidget(self.thresholdSpinBox)
        hbox.addWidget(self.offsetSpinBox)
        layout.addLayout(hbox, 0, 1, 1, 2)
        layout.addWidget(self.cutLabel, 1, 0)
        layout.addWidget(self.cutListView, 1, 1, 1, 2)
        layout.addWidget(self.filterWidget, 2, 1)
        layout.addWidget(self.addCutButton, 2, 2)
        layout.addWidget(self.infoTextEdit, 0, 3, 3, 1)
        layout.addWidget(self.buttonBox, 3, 0, 1, 4)
        self.setLayout(layout)

    def updateObjectType(self):
        """Update inputs according to selected object type."""
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
            QtWidgets.QMessageBox.critical(self,
                self.tr("Failed to load scales"),
                pyqt4_str(self.tr("Missing scales for object of type {0}")).format(objectType),
            )
            return
        self.thresholdSpinBox.setRange(float(scale[kMinimum]), float(scale[kMaximum]))
        self.thresholdSpinBox.setSingleStep(float(scale[kStep]))
        self.updateInfoText()
        self.initCuts()
        # Toggle cut creation button (disable if no cuts available for object type).
        specs = CutSpecs.query(object=self.objectType())
        self.addCutButton.setEnabled(len(specs))

    def initObjectList(self, objects):
        """Initialize list of available objects. Ignores objects with no scales."""
        for index, name in enumerate(ObjectTypes):
            if name not in objects:
                continue # ignore if not in init list
            self.typeComboBox.addItem(miniIcon(name.lower()), name)
            if not self.getScale(name): # on missing scale (editing outdated XML?)
                self.typeComboBox.setItemEnabled(index, False)

    def initCuts(self):
        """Initialize list of checkable cuts."""
        self.cutModel = QtGui.QStandardItemModel(self)
        self.cutModel._items = []
        for cut in sorted(self.menu.cuts, key=lambda cut: cut.name):
            if cut.object == self.objectType():
                label = fCutLabel(cut)
                item = CutItem(label)
                item.setData(cut)
                if cut.modified:
                    font = item.font()
                    font.setWeight(QtGui.QFont.Bold)
                    item.setFont(font)
                self.cutModel.appendRow(item)
                self.cutModel._items.append(item)
        self.cutProxy = QtCore.QSortFilterProxyModel(self)
        self.cutProxy.setFilterKeyColumn(-1) # Filter all collumns
        self.cutProxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.cutProxy.setSourceModel(self.cutModel)
        self.cutModel.itemChanged.connect(self.updateInfoText)
        self.cutListView.setModel(self.cutProxy)
        self.filterWidget.textChanged.connect(self.updateFilter)

    def getScale(self, objectType):
        """Returns scale for object or None if not found."""
        # Get only scales of object type
        scales = list(filter(lambda item: item[kObject] == objectType, self.menu.scales.scales))
        # Get only threshold/count scales
        return (list(filter(lambda item: item[kType] in (kET, kCOUNT, ), scales)) or [None])[0]

    def updateFilter(self, text):
        """Update cut filter."""
        self.cutListView.model().setFilterWildcard(text)

    def objectType(self):
        """Returns object type."""
        return pyqt4_str(self.typeComboBox.currentText())

    def comparisonOperator(self):
        """Returns comparison operator."""
        return pyqt4_str(pyqt4_toPyObject(self.compareComboBox.itemData(self.compareComboBox.currentIndex())))

    def threshold(self):
        """Returns objects threshold."""
        return self.thresholdSpinBox.value()

    def bxOffset(self):
        return self.offsetSpinBox.value()

    def selectedCuts(self):
        """Retruns list of checked cut names."""
        return [pyqt4_str(pyqt4_toPyObject(item.data()).name) for item in list(filter(lambda item: item.checkState() == QtCore.Qt.Checked, self.cutModel._items))]

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
        object_ = toObject(token)
        if object_.type not in self.objectTypes:
            raise ValueError("Invalid object type.")
        object_.cuts = objectCuts(token)
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(object_.type))
        self.compareComboBox.setCurrentIndex(self.compareComboBox.findData(object_.comparison_operator))
        self.thresholdSpinBox.setValue(object_.decodeThreshold())
        self.offsetSpinBox.setValue(object_.bx_offset)
        for cut in self.cutModel._items:
            if pyqt4_toPyObject(cut.data()).name in object_.cuts:
                cut.setCheckState(QtCore.Qt.Checked)

    def addCut(self):
        """Raise cut editor to add a new cut."""
        # Load cut settings only for selected object type
        dialog = CutEditorDialog(self.menu, self)
        specs = CutSpecs.query(object=self.objectType())
        dialog.setupCuts(specs)
        dialog.setModal(True)
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        new_cut = dialog.newCut()
        self.menu.addCut(new_cut)
        # TODO code refactoring!
        # Restore selected cuts and newly added one.
        selectedCuts = self.selectedCuts()
        self.initCuts()
        # TODO code refactoring!
        # Restore selected cuts and newly added one.
        for cut in self.cutModel._items:
            if pyqt4_str(pyqt4_toPyObject(cut.data()).name) in selectedCuts:
                cut.setCheckState(QtCore.Qt.Checked)
            # Select newly added cut
            if pyqt4_str(pyqt4_toPyObject(cut.data()).name) == new_cut.name:
                cut.setCheckState(QtCore.Qt.Checked)
