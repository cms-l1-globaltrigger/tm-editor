#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import tmGrammar
from tmEditor import Toolbox
from tmEditor.Menu import (
    toObject,
    thresholdFloat,
)
from tmEditor.CommonWidgets import (
    PrefixedSpinBox,
    FilterLineEdit,
    ComboBoxPlus,
)

import sys, os

__all__ = ['ObjectEditorDialog', ]

ThresholdObjects = [
    tmGrammar.MU,
    tmGrammar.EG,
    tmGrammar.JET,
    tmGrammar.TAU,
    tmGrammar.ETM,
    tmGrammar.HTM,
    tmGrammar.ETT,
    tmGrammar.HTT,
    tmGrammar.ETTEM,
    tmGrammar.ETMHF,
]
"""Ordered list of ET threshold type object names."""

CountObjects = [
    tmGrammar.MBT0HFP,
    tmGrammar.MBT1HFP,
    tmGrammar.MBT0HFM,
    tmGrammar.MBT1HFM,
]
"""Ordered list of COUNT type object names."""

Objects = ThresholdObjects + CountObjects
"""Ordered list of all object type names."""

ObjectCuts = [
    tmGrammar.ETA,
    tmGrammar.PHI,
    tmGrammar.ISO,
    tmGrammar.QLTY,
    tmGrammar.CHG,
]
"""Orderd list of cut type names."""

def cutItem(text, checked = False):
    """Retruns a checkable cut standard item, to be inserted to a list model."""
    item = QStandardItem(text)
    item.setEditable(False)
    item.setCheckable(True)
    if checked:
        item.setCheckState(Qt.Checked)
    return item

class ObjectEditorDialog(QDialog):
    """Object editor dialog class."""

    def __init__(self, menu, parent = None):
        """Constructor, takes a reference to a menu and an optional parent."""
        super(ObjectEditorDialog, self).__init__(parent)
        self.menu = menu
        self.ui = ObjectEditorUi(self)
        self.initObjectList(menu)
        self.initCuts()
        self.updateObjectType()
        # Connect signals
        self.ui.typeComboBox.currentIndexChanged.connect(self.updateObjectType)
        self.ui.compareComboBox.currentIndexChanged.connect(self.updateInfoText)
        self.ui.thresholdSpinBox.valueChanged.connect(self.updateInfoText)
        self.ui.offsetSpinBox.valueChanged.connect(self.updateInfoText)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        # self.ui.buttonBox.helpRequested.connect(self.showHelp)
        self.updateInfoText()

    def updateObjectType(self):
        objectType = self.objectType()
        if objectType in ThresholdObjects:
            self.ui.thresholdSpinBox.setSuffix(" GeV")
            self.ui.thresholdSpinBox.setDecimals(1)
        elif objectType in CountObjects:
            self.ui.thresholdSpinBox.setDecimals(0)
            self.ui.thresholdSpinBox.setSuffix("")
        scale = self.getScale(objectType)
        # Just to make sure...
        if scale is None:
            QMessageBox.critical(self,
                self.tr("Failed to load scales"),
                QString("Missing scales for object of type %1").arg(objectType),
            )
            return
        self.ui.thresholdSpinBox.setRange(float(scale['minimum']), float(scale['maximum']))
        self.ui.thresholdSpinBox.setSingleStep(float(scale['step']))
        self.updateInfoText()
        self.initCuts()

    def initObjectList(self, menu):
        """Initialize list of available objects. Ignores objects with no scales."""
        for index, name in enumerate(Objects):
            self.ui.typeComboBox.addItem(name)
            if not self.getScale(name): # on missing scale (editng outdated XML?)
                self.ui.typeComboBox.setItemEnabled(index, False)

    def initCuts(self):
        """Initialize list of checkable cuts."""
        self.cutModel = QStandardItemModel(self)
        self.cutModel._items = []
        for cut in self.menu.cuts:
            if cut.object == self.objectType():
                item = cutItem(cut.name)
                self.cutModel.appendRow(item)
                self.cutModel._items.append(item)
        self.cutProxy = QSortFilterProxyModel(self)
        self.cutProxy.setFilterKeyColumn(-1) # Filter all collumns
        self.cutProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.cutProxy.setSourceModel(self.cutModel)
        self.cutModel.itemChanged.connect(self.updateInfoText)
        self.ui.cutListView.setModel(self.cutProxy)
        self.ui.filterLineEdit.textChanged.connect(self.updateFilter)

    def getScale(self, objectType):
        """Returns scale for object or None if not found."""
        # Get only scales of object type
        scales = filter(lambda item: item['object'] == objectType, self.menu.scales.scales)
        # Get only threshold/count scales
        return (filter(lambda item: item['type'] in ('ET', 'COUNT', ), scales) or [None])[0]

    def updateFilter(self, text):
        """Update cut filter."""
        self.ui.cutListView.model().setFilterWildcard(text)

    def objectType(self):
        """Returns object type."""
        return str(self.ui.typeComboBox.currentText())

    def comparisonType(self):
        """Returns comparison type."""
        return str(self.ui.compareComboBox.itemData(self.ui.compareComboBox.currentIndex()).toPyObject())

    def thresholdExpr(self):
        """Returns formatted object threshold."""
        return 'p'.join(format(float(self.ui.thresholdSpinBox.value()), '.1f').split('.')).replace('p0', '')

    def selectedCuts(self):
        """Retruns list of checked cuts."""
        return [str(item.text()) for item in filter(lambda item: item.checkState() == Qt.Checked, self.cutModel._items)]

    def toExpression(self):
        """Returns object expression selected by the inputs."""
        expression = [self.objectType()]
        if self.comparisonType() != tmGrammar.GE:
            expression.append(self.comparisonType())
        expression.append(self.thresholdExpr())
        offset = self.ui.offsetSpinBox.value()
        if offset != 0:
            expression.append(format(offset, '+d'))
        # Compile list of cuts
        cuts = self.selectedCuts()
        if cuts:
            expression.append('[')
            buffer = []
            for cut in cuts:
                buffer.append(cut)
            expression.append(', '.join(buffer))
            expression.append(']')
        return ''.join(expression)

    def updateInfoText(self):
        """Update info box text."""
        objectType = self.objectType()
        scale = self.getScale(objectType)
        minThreshold = float(scale['minimum'])
        maxThreshold = float(scale['maximum'])
        step = float(scale['step'])
        expression = self.toExpression()
        text = []
        text.append('<h3>{objectType} Object Requirement</h3>')
        if objectType in ThresholdObjects:
            text.append('<p>Valid threshold: {minThreshold:.1f} GeV - {maxThreshold:.1f} GeV ({step:.1f} GeV steps)</p>')
        elif objectType in CountObjects:
            text.append('<p>Valid count: {minThreshold:.0f} - {maxThreshold:.0f}</p>')
        text.append('<h4>Preview</h4>')
        text.append('<p><pre>{expression}</pre></p>')
        self.ui.infoTextEdit.setText(''.join(text).format(**locals()))

    def showHelp(self):
        # TODO
        pass

    def loadObject(self, object):
        """Load dialog by values from object. Will raise a ValueError if string
        *object* is not a valid object.
        """
        object = toObject(str(object))
        self.ui.typeComboBox.setCurrentIndex(self.ui.typeComboBox.findText(object.type))
        self.ui.thresholdSpinBox.setValue(thresholdFloat(object.threshold))
        self.ui.offsetSpinBox.setValue(int(object.bx_offset))

class ObjectEditorUi(object):
    """User interface for class ObjectEditor."""

    def __init__(self, context):
        context.setWindowTitle(context.tr("Object Editor"))
        context.resize(640, 380)
        self.objectLabel = QLabel(context.tr("Object"), context)
        self.objectLabel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.typeComboBox = ComboBoxPlus(context)
        self.typeComboBox.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.compareComboBox = QComboBox(context)
        self.compareComboBox.addItem('=>', tmGrammar.GE)
        self.compareComboBox.addItem('==', tmGrammar.EQ)
        self.thresholdSpinBox = QDoubleSpinBox(context)
        self.thresholdSpinBox.setDecimals(1)
        self.thresholdSpinBox.setSingleStep(.5)
        self.thresholdSpinBox.setSuffix(context.tr(" GeV"))
        self.offsetSpinBox = PrefixedSpinBox(context)
        self.offsetSpinBox.setRange(-2, 2)
        self.offsetSpinBox.setValue(0)
        self.offsetSpinBox.setSuffix(context.tr(" BX"))
        self.cutLabel = QLabel(context.tr("Cuts"), context)
        self.cutLabel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.cutListView = QListView(context)
        self.cutListView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cutListView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.filterLabel = QLabel(context.tr("Filter"), context)
        self.filterLabel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.filterLineEdit = FilterLineEdit(context)
        self.infoTextEdit = QTextEdit(context)
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.buttonBox = QDialogButtonBox(context)
        #self.buttonBox.setStandardButtons(QDialogButtonBox.Help|QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        layout = QGridLayout()
        layout.addWidget(self.objectLabel, 0, 0)
        hbox = QHBoxLayout()
        hbox.addWidget(self.typeComboBox)
        hbox.addWidget(self.compareComboBox)
        hbox.addWidget(self.thresholdSpinBox)
        hbox.addWidget(self.offsetSpinBox)
        layout.addLayout(hbox, 0, 1)
        layout.addWidget(self.cutLabel, 1, 0)
        layout.addWidget(self.cutListView, 1, 1)
        hbox = QHBoxLayout()
        hbox.addWidget(self.filterLabel)
        hbox.addWidget(self.filterLineEdit)
        layout.addLayout(hbox, 2, 1)
        layout.addWidget(self.infoTextEdit, 0, 2, 3, 1)
        layout.addWidget(self.buttonBox, 3, 0, 1, 3)
        context.setLayout(layout)

if __name__ == '__main__':
    import sys
    from tmEditor import Menu
    app = QApplication(sys.argv)
    menu = Menu(sys.argv[1])
    window = ObjectEditor(menu)
    window.show()
    sys.exit(app.exec_())
