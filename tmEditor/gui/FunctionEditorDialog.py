#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import tmGrammar

from tmEditor.core import Toolbox
from tmEditor.core.AlgorithmHelper import AlgorithmHelper
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError

# Common widgets
from tmEditor.gui.CommonWidgets import PrefixedSpinBox
from tmEditor.gui.CommonWidgets import TextFilterWidget
from tmEditor.gui.CommonWidgets import ComboBoxPlus

from ObjectEditorDialog import ObjectEditorDialog, cutItem

# Qt4 python bindings
from PyQt4 import QtCore
from PyQt4 import QtGui

import sys, os
import re

__all__ = ['FunctionEditorDialog', ]

# -----------------------------------------------------------------------------
#  Function editor dialog class
# -----------------------------------------------------------------------------

class FunctionEditorDialog(QtGui.QDialog):
    ObjectReqs = 4

    def __init__(self, menu, parent=None):
        super(FunctionEditorDialog, self).__init__(parent)
        self.menu = menu
        self.validator = AlgorithmSyntaxValidator(menu)
        self.setupUi()
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.updateCuts()
        self.updateInfoText()

    def setupUi(self):
        self.setWindowIcon(Toolbox.createIcon("wizard-function"))
        self.setWindowTitle(self.tr("Function Editor"))
        self.functionComboBox = QtGui.QComboBox(self)
        self.functionComboBox.addItem(self.tr("%1 (combination)").arg(tmGrammar.comb), tmGrammar.comb)
        self.functionComboBox.addItem(self.tr("%1 (correlation)").arg(tmGrammar.dist), tmGrammar.dist)
        self.functionComboBox.addItem(self.tr("%1 (invariant mass)").arg(tmGrammar.mass), tmGrammar.mass)
        self.functionComboBox.currentIndexChanged.connect(self.onUpdateObjectHelpers)
        self.objectHelpers = [FunctionReqHelper(i, self) for i in range(self.ObjectReqs)]
        self.cutListView = QtGui.QListView(self)
        self.cutListView.activated.connect(self.updateInfoText)
        self.cutListView.clicked.connect(self.updateInfoText)
        self.filterWidget = TextFilterWidget(self)
        self.infoTextEdit = QtGui.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel(self.tr("Function"), self), 0, 0)
        layout.addWidget(self.functionComboBox, 0, 1, 1, 2)
        for helper in self.objectHelpers:
            layout.addWidget(helper.label, 1+helper.index, 0)
            layout.addWidget(helper.lineEdit, 1+helper.index, 1)
            layout.addWidget(helper.editButton, 1+helper.index, 2)
            helper.lineEdit.textChanged.connect(self.updateInfoText)
        layout.addWidget(QtGui.QLabel(self.tr("Cuts"), self), 5, 0)
        layout.addWidget(self.cutListView, 5, 1, 1, 2)
        layout.addWidget(self.filterWidget, 6, 1, 1, 2)
        layout.addWidget(self.infoTextEdit, 0, 3, 7, 1)
        layout.addWidget(self.buttonBox, 7, 0, 1, 4)
        self.setLayout(layout)

    def functionType(self):
        """Returns function type."""
        comboBox = self.functionComboBox
        return str(comboBox.itemData(comboBox.currentIndex()).toPyObject())

    def selectedCuts(self):
        """Retruns list of checked cut names."""
        return [str(item.text()) for item in filter(lambda item: item.checkState() == QtCore.Qt.Checked, self.cutModel._items)]

    def onUpdateObjectHelpers(self, index):
        self.updateCuts()
        for helper in self.objectHelpers:
            helper.setEnabled(True)
            if self.functionType() in (tmGrammar.dist, tmGrammar.mass) and helper.index >= 2:
                helper.setEnabled(False)

        self.updateInfoText()

    def updateCuts(self):
        """Initialize list of checkable cuts."""
        self.cutModel = QtGui.QStandardItemModel(self)
        self.cutModel._items = []
        for cut in sorted(self.menu.cuts, key=lambda cut: cut.name):
            if cut.object == self.functionType():
                item = cutItem(cut.name)
                self.cutModel.appendRow(item)
                self.cutModel._items.append(item)
        self.cutProxy = QtGui.QSortFilterProxyModel(self)
        self.cutProxy.setFilterKeyColumn(-1) # Filter all collumns
        self.cutProxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.cutProxy.setSourceModel(self.cutModel)
        ###self.cutModel.itemChanged.connect(self.updateInfoText)
        self.cutListView.setModel(self.cutProxy)
        self.filterWidget.textChanged.connect(self.updateFilter)

    def updateFilter(self, text):
        """Update cut filter."""
        self.cutListView.model().setFilterWildcard(text)

    def updateInfoText(self):
        """Update info box text."""
        functionType = self.functionType()
        expression = self.expression()
        text = []
        text.append('<h3>{functionType} Function</h3>')
        text.append('<h4>Preview</h4>')
        text.append('<p><pre>{expression}</pre></p>')
        self.infoTextEdit.setText(''.join(text).format(**locals()))

    def expression(self):
        """Returns expression selected by the inputs."""
        expression = AlgorithmHelper()
        objects = []
        for helper in self.objectHelpers:
            if helper.isValid():
                objects.append(helper.lineEdit.text())
        expression.addFunction(self.functionType(), objects=objects, cuts=self.selectedCuts())
        return AlgorithmFormatter.normalize(expression.serialize())

    def loadFunction(self, token):
        """Load dialog by values from function. Will raise a ValueError if string
        *token* is not a valid object.
        """
        f = tmGrammar.Function_Item()
        if not tmGrammar.Function_parser(AlgorithmFormatter.compress(token), f):
            raise ValueError(token)
        self.functionComboBox.setCurrentIndex(self.functionComboBox.findData(f.name))
        objects = list(tmGrammar.Function_getObjects(f))
        for i, cuts in enumerate(tmGrammar.Function_getObjectCuts(f)):
            if cuts:
                objects[i] = "{object}[{cuts}]".format(object=objects[i], cuts=cuts)
        for helper in self.objectHelpers:
            if helper.index < len(objects):
                helper.lineEdit.setText(objects[helper.index])
            else:
                helper.lineEdit.clear()
        for cut in self.cutModel._items:
            if cut.text() in tmGrammar.Function_getCuts(f):
                cut.setCheckState(QtCore.Qt.Checked)

    def accept(self):
        """Very preliminary validation."""
        try:
            self.validator.validate(AlgorithmFormatter.compress(self.expression()))
        except AlgorithmSyntaxError, e:
            QtGui.QMessageBox.warning(self, self.tr("Invalid expression"),
                self.tr("Invalid expression `%1'. %2").arg(e.token or ""),
            )
            return
        super(FunctionEditorDialog, self).accept()

# -----------------------------------------------------------------------------
#  Function requirement helper class
# -----------------------------------------------------------------------------

class FunctionReqHelper(object):

    def __init__(self, index, parent):
        self.index = index
        self.parent = parent
        self.label = QtGui.QLabel(parent.tr("Req. %1").arg(index+1))
        self.lineEdit = QtGui.QLineEdit(parent)
        self.editButton = QtGui.QToolButton(parent)
        self.editButton.setText(parent.tr("..."))
        self.editButton.clicked.connect(self.edit)

    def isValid(self):
        """Retruns True if helper is enabled and contains input."""
        return self.lineEdit.isEnabled() and self.lineEdit.text()

    def setEnabled(self, enabled):
        self.label.setEnabled(enabled)
        self.lineEdit.setEnabled(enabled)
        self.editButton.setEnabled(enabled)

    def edit(self):
        dialog = ObjectEditorDialog(self.parent.menu, self.parent)
        token = str(self.lineEdit.text())
        if token: # else start with empty editor
            dialog.loadObject(token)
        dialog.exec_()
        if dialog.result() == QtGui.QDialog.Accepted:
            self.lineEdit.setText(dialog.expression())

# -----------------------------------------------------------------------------
#  Unit test
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from tmEditor import Menu
    app = QtGui.QApplication(sys.argv)
    menu = Menu(sys.argv[1])
    window = FunctionEditor(menu)
    window.show()
    sys.exit(app.exec_())
