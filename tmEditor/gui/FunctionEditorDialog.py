#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import tmGrammar

from tmEditor.core import Toolbox
from tmEditor.core import Settings

from tmEditor.core.AlgorithmHelper import AlgorithmHelper
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError

# Common widgets
from tmEditor.gui.CommonWidgets import PrefixedSpinBox
from tmEditor.gui.CommonWidgets import TextFilterWidget
from tmEditor.gui.CommonWidgets import ComboBoxPlus
from tmEditor.gui.CommonWidgets import createIcon

from tmEditor.gui.CutEditorDialog import CutEditorDialog
from tmEditor.gui.ObjectEditorDialog import ObjectEditorDialog, CutItem, getCutSettings

# Qt4 python bindings
from tmEditor.PyQt5Proxy import QtCore
from tmEditor.PyQt5Proxy import QtGui
from tmEditor.PyQt5Proxy import QtWidgets
from tmEditor.PyQt5Proxy import pyqt4_toPyObject, pyqt4_str

import sys, os
import re

__all__ = ['FunctionEditorDialog', ]

# -----------------------------------------------------------------------------
#  Function editor dialog class
# -----------------------------------------------------------------------------

class FunctionEditorDialog(QtWidgets.QDialog):
    ObjectReqs = 4

    def __init__(self, menu, parent=None):
        super(FunctionEditorDialog, self).__init__(parent)
        self.menu = menu
        self.validator = AlgorithmSyntaxValidator(menu)
        self.setupUi()
        self.addCutButton.clicked.connect(self.addCut)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # Initialize
        self.updateCuts()
        self.updateInfoText()

    def setupUi(self):
        self.setWindowIcon(createIcon("wizard-function"))
        self.setWindowTitle(self.tr("Function Editor"))
        self.functionComboBox = QtWidgets.QComboBox(self)
        self.functionComboBox.addItem(pyqt4_str(self.tr("{0} (combination)")).format(tmGrammar.comb), tmGrammar.comb)
        self.functionComboBox.addItem(pyqt4_str(self.tr("{0} (correlation)")).format(tmGrammar.dist), tmGrammar.dist)
        self.functionComboBox.addItem(pyqt4_str(self.tr("{0} (invariant mass)")).format(tmGrammar.mass), tmGrammar.mass)
        self.functionComboBox.currentIndexChanged.connect(self.onUpdateObjectHelpers)
        self.objectHelpers = [FunctionReqHelper(i, self) for i in range(self.ObjectReqs)]
        self.cutListView = QtWidgets.QListView(self)
        self.cutListView.activated.connect(self.updateInfoText)
        self.cutListView.clicked.connect(self.updateInfoText)
        self.filterWidget = TextFilterWidget(self)
        self.addCutButton = QtWidgets.QPushButton(createIcon("list-add"), self.tr("Add..."), self)
        self.infoTextEdit = QtWidgets.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel(self.tr("Function"), self), 0, 0)
        layout.addWidget(self.functionComboBox, 0, 1, 1, 2)
        for helper in self.objectHelpers:
            layout.addWidget(helper.label, 1+helper.index, 0)
            layout.addWidget(helper.lineEdit, 1+helper.index, 1)
            layout.addWidget(helper.editButton, 1+helper.index, 2)
            helper.lineEdit.textChanged.connect(self.updateInfoText)
        layout.addWidget(QtWidgets.QLabel(self.tr("Cuts"), self), 5, 0)
        layout.addWidget(self.cutListView, 5, 1, 1, 2)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filterWidget)
        hbox.addWidget(self.addCutButton)
        layout.addLayout(hbox, 6, 1, 1, 2)
        layout.addWidget(self.infoTextEdit, 0, 3, 7, 1)
        layout.addWidget(self.buttonBox, 7, 0, 1, 4)
        self.setLayout(layout)

    def functionType(self):
        """Returns function type."""
        comboBox = self.functionComboBox
        return pyqt4_str(pyqt4_toPyObject(comboBox.itemData(comboBox.currentIndex())))

    def selectedCuts(self):
        """Retruns list of checked cut names."""
        return [pyqt4_str(pyqt4_toPyObject(item.data()).name) for item in list(filter(lambda item: item.checkState() == QtCore.Qt.Checked, self.cutModel._items))]

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
                if cut.data:
                    label = "{0} ({1})".format(cut.name, cut.data)
                else:
                    label = "{0} ({1:.3f}-{2:.3f})".format(cut.name, cut.minimum, cut.maximum)
                item = CutItem(label)
                item.setData(cut)
                self.cutModel.appendRow(item)
                self.cutModel._items.append(item)
        self.cutProxy = QtCore.QSortFilterProxyModel(self)
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
                objects.append(helper.text())
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
            if pyqt4_str(pyqt4_toPyObject(cut.data()).name) in tmGrammar.Function_getCuts(f):
                cut.setCheckState(QtCore.Qt.Checked)

    def addCut(self):
        """Raise cut editor to add a new cut."""
        # Load cut settings only for selected function type.
        dialog = CutEditorDialog(self.menu, getCutSettings(self.functionType()), self)
        dialog.setModal(True)
        dialog.updateEntries()
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        cut = dialog.newCut()
        self.menu.addCut(cut)
        #self.cutsPage.top.model().setSourceModel(self.cutsPage.top.model().sourceModel())
        #self.updateBottom()
        # TODO self.menu.setModified(True)
        #self.modified.emit()
        # Select new entry TODO: better to implement insertRow in model!
        #proxy = item.top.model()
        #for row in range(proxy.rowCount()):
        #    index = proxy.index(row, 0)
        #    if pyqt4_toPyObject(index.data()) == cut.name:
        #        item.top.setCurrentIndex(index)
        #        break
        expression = self.expression()
        self.updateCuts()
        try:
            self.loadFunction(expression)
        except ValueError:
            pass

    def accept(self):
        """Very preliminary validation."""
        # Get object requirements
        helpers = [helper for helper in self.objectHelpers if helper.isValid()]
        # Check minimum required objects
        if len(helpers) < 2:
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"),
                pyqt4_str(self.tr("Function {0}{{...}} requires at least two object requirements.")).format(self.functionType())
            )
            return
        # Validate object requirements.
        for helper in helpers:
            try:
                self.validator.validate(AlgorithmFormatter.compress(helper.text()))
            except AlgorithmSyntaxError as e:
                QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"),
                    pyqt4_str(self.tr("Invalid object requirement: {0}")).foramt(pyqt4_str(helper.text()))
                )
                return
        # Check required cuts
        if self.functionType() in (tmGrammar.dist, tmGrammar.mass):
            if len(self.selectedCuts()) < 1:
                QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"),
                    pyqt4_str(self.tr("Function {0}{{...}} requires at least one function cut.")).format(self.functionType())
                )
                return
        # Validate whole expression
        try:
            self.validator.validate(AlgorithmFormatter.compress(self.expression()))
        except AlgorithmSyntaxError as e:
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"),
                pyqt4_str(self.tr("Invalid expression: {0}")).format(e.token or format(e)),
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
        self.label = QtWidgets.QLabel(pyqt4_str(parent.tr("Req. {0}")).format(index+1))
        self.lineEdit = QtWidgets.QLineEdit(parent)
        self.editButton = QtWidgets.QToolButton(parent)
        self.editButton.setText(parent.tr("..."))
        self.editButton.clicked.connect(self.edit)

    def text(self):
        """Returns text of line edit."""
        return pyqt4_str(self.lineEdit.text())

    def isValid(self):
        """Retruns True if helper is enabled and contains input."""
        return self.lineEdit.isEnabled() and self.text()

    def setEnabled(self, enabled):
        self.label.setEnabled(enabled)
        self.lineEdit.setEnabled(enabled)
        self.editButton.setEnabled(enabled)

    def edit(self):
        dialog = ObjectEditorDialog(self.parent.menu, self.parent)
        token = self.text()
        if token: # else start with empty editor
            try:
                dialog.loadObject(token)
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self.parent, self.parent.tr("Invalid expression"),
                    pyqt4_str(self.parent.tr("Invalid object expression: {0}")).format(e),
                )
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.lineEdit.setText(dialog.expression())

# -----------------------------------------------------------------------------
#  Unit test
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from tmEditor import Menu
    app = QtWidgets.QApplication(sys.argv)
    menu = Menu(sys.argv[1])
    window = FunctionEditor(menu)
    window.show()
    sys.exit(app.exec_())
