"""Function editor dialog."""

from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

import tmGrammar

from tmEditor.core.formatter import fCutLabel
from tmEditor.core.Settings import CutSpecs
from tmEditor.core.types import ObjectTypes

from tmEditor.core.AlgorithmHelper import AlgorithmHelper
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError

# Common widgets
from tmEditor.gui.CommonWidgets import TextFilterWidget
from tmEditor.gui.CommonWidgets import createIcon

from tmEditor.gui.CutEditorDialog import CutEditorDialog
from tmEditor.gui.ObjectEditorDialog import ObjectEditorDialog, CutItem

__all__ = ['FunctionEditorDialog', ]

Functions = {
    tmGrammar.comb: {"objects": 4, "label": "combination", "description": "Object combinations (di- tri- quad- objects)."},
    tmGrammar.dist: {"objects": 2, "label": "correlation", "description": "Topological distance (correlation) of two object requirements."},
    tmGrammar.mass_inv: {"objects": 2, "label": "invariant mass", "description": "Invariant mass of two object requirements."},
    tmGrammar.mass_inv_upt: {"objects": 2, "label": "invariant mass unconstrained pt", "description": "Invariant mass for unconstained pt of two muon requirements."},
    tmGrammar.mass_inv_dr: {"objects": 2, "label": "invariant mass/delta-R", "description": "Invariant mass/delta-R of two object requirements."},
    tmGrammar.mass_inv_3: {"objects": 3, "label": "invariant mass of 3 particles", "description": "Invariant mass of three object requirements."},
    tmGrammar.mass_trv: {"objects": 2, "label": "transverse mass", "description": "Transverse mass correlation of two object requirements (at least on without eta component)."},
    tmGrammar.comb_orm: {"objects": 5, "label": "combination + overlap removal", "description": "Object combinations with overlap removal."},
    tmGrammar.dist_orm: {"objects": 3, "label": "correlation + overlap removal", "description": "Topological distance (correlation) of two object requirements with overlap removal."},
    tmGrammar.mass_inv_orm: {"objects": 3, "label": "invariant mass + overlap removal", "description": "Invariant mass correlation of two object requirements with overlap removal."},
}


def hasOverlapRemoval(name):
    """Return True if function name provides an overlap removal."""
    return name in (
        tmGrammar.comb_orm,
        tmGrammar.dist_orm,
        tmGrammar.mass_inv_orm,
        tmGrammar.mass_inv_orm,
    )


# -----------------------------------------------------------------------------
#  Function editor dialog class
# -----------------------------------------------------------------------------

class FunctionEditorDialog(QtWidgets.QDialog):

    ObjectReqs = 5

    def __init__(self, menu, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.menu = menu
        self.validator = AlgorithmSyntaxValidator(menu)
        self.setupUi()
        self.functionComboBox.currentIndexChanged.connect(self.onUpdateObjectHelpers)
        self.addCutButton.clicked.connect(self.addCut)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # Initialize
        self.updateCuts()
        self.updateInfoText()
        # Trigger slots
        self.onUpdateObjectHelpers(0) # glitch

    def setupUi(self):
        self.setWindowIcon(createIcon("wizard-function"))
        self.setWindowTitle(self.tr("Function Editor"))
        self.functionComboBox = QtWidgets.QComboBox(self)
        for key, value in Functions.items():
            label = value.get("label", "")
            self.functionComboBox.addItem(f"{key} ({label})", key)
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
            layout.addWidget(helper.label, 1 + helper.index, 0)
            layout.addWidget(helper.lineEdit, 1 + helper.index, 1)
            layout.addWidget(helper.editButton, 1 + helper.index, 2)
            helper.lineEdit.textChanged.connect(self.updateInfoText)
        layout.addWidget(QtWidgets.QLabel(self.tr("Cuts"), self), 6, 0)
        layout.addWidget(self.cutListView, 6, 1, 1, 2)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filterWidget)
        hbox.addWidget(self.addCutButton)
        layout.addLayout(hbox, 7, 1, 1, 2)
        layout.addWidget(self.infoTextEdit, 0, 3, 7, 1)
        layout.addWidget(self.buttonBox, 8, 0, 1, 4)
        self.setLayout(layout)

    def functionType(self):
        """Returns function type."""
        comboBox = self.functionComboBox
        return comboBox.itemData(comboBox.currentIndex())

    def selectedCuts(self):
        """Retruns list of checked cut names."""
        return [item.data().name for item in list(filter(lambda item: item.checkState() == QtCore.Qt.Checked, self.cutModel._items))]

    def onUpdateObjectHelpers(self, index):
        """Update object helper widgets."""
        self.updateCuts()
        functionType = self.functionType()
        for helper in self.objectHelpers:
            # Enable all object types
            helper.types = ObjectTypes
            # Disable helpers if not supported
            count = Functions.get(functionType, {}).get("objects", 0)
            helper.setEnabled(helper.index < count)
            # Set object types for object dialog
            if hasOverlapRemoval(functionType):
                helper.types = (tmGrammar.EG, tmGrammar.TAU, tmGrammar.JET)
        self.updateInfoText()

    def updateCuts(self):
        """Initialize list of checkable cuts."""
        self.cutModel = QtGui.QStandardItemModel(self)
        self.cutModel._items = []
        # Calculate supported cut types.
        cutTypes = []
        for spec in CutSpecs:
            if spec.enabled:
                if spec.functions and self.functionType() in spec.functions:
                    cutTypes.append(spec.type)
        for cut in sorted(self.menu.cuts, key=lambda cut: cut.name):
            if cut.type in cutTypes:
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
        ###self.cutModel.itemChanged.connect(self.updateInfoText)
        self.cutListView.setModel(self.cutProxy)
        self.filterWidget.textChanged.connect(self.updateFilter)

    def updateFilter(self, text):
        """Update cut filter."""
        self.cutListView.model().setFilterWildcard(text)

    def updateInfoText(self):
        """Update info box text."""
        functionType = self.functionType()
        expression = AlgorithmFormatter.expand(self.expression())
        text = []
        text.append(f'<h3>{functionType} Function</h3>')
        description = Functions.get(functionType, {}).get("description")
        if description:
            text.append(f"<p>{description}</p>")
        if hasOverlapRemoval(functionType):
            text.append(f'<p>The <em>last</em> object requirement must be of a different type, applying the overlap removal on the <em>preceding</em> object requirement(s).</p>')
        text.append(f'<h4>Preview</h4>')
        text.append(f'<p><pre>{expression}</pre></p>')
        self.infoTextEdit.setText(''.join(text))

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
            if cut.data().name in tmGrammar.Function_getCuts(f):
                cut.setCheckState(QtCore.Qt.Checked)
        self.updateInfoText() # refresh

    def addCut(self):
        """Raise cut editor to add a new cut."""
        # TODO code refactoring!
        # Load cut settings only for selected function type.
        specs = []
        for spec in CutSpecs:
            if spec.enabled:
                if spec.functions and self.functionType() in spec.functions:
                    specs.append(spec)
        # Remove duplicates, sort in original order.
        specs = sorted(set(specs), key=lambda spec: CutSpecs.specs.index(spec))
        # Create dialog
        dialog = CutEditorDialog(self.menu, self)
        dialog.setupCuts(specs)
        dialog.treeWidget.expandAll() # show all sub items
        dialog.setModal(True)
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        # Add new cut to menu
        new_cut = dialog.newCut()
        self.menu.addCut(new_cut)
        # TODO code refactoring!
        # Remember selected cuts before re-initalizing cut list.
        selectedCuts = self.selectedCuts()
        self.updateCuts()
        # TODO code refactoring!
        # Restore selected cuts and newly added one.
        for cut in self.cutModel._items:
            if cut.data().name in selectedCuts:
                cut.setCheckState(QtCore.Qt.Checked)
            # Select newly create cut
            if cut.data().name == new_cut.name:
                cut.setCheckState(QtCore.Qt.Checked)
        try:
            self.loadFunction(self.expression())
        except ValueError:
            pass

    def accept(self):
        """Validate content before grant accept."""
        # TODO code refactoring!
        # Get object requirements
        helpers = [helper for helper in self.objectHelpers if helper.isValid()]
        # Check minimum required objects
        if self.functionType() == tmGrammar.mass_inv_3:
            if len(helpers) < 3:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid expression"),
                    self.tr("Function {0}{{...}} requires at three object requirements.").format(self.functionType())
                )
                return
        else:
            if len(helpers) < 2:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid expression"),
                    self.tr("Function {0}{{...}} requires at least two object requirements.").format(self.functionType())
                )
                return
        # Validate object requirements.
        for helper in helpers:
            try:
                self.validator.validate(AlgorithmFormatter.compress(helper.text()))
            except AlgorithmSyntaxError as exc:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid expression"),
                    self.tr("Invalid object requirement {0}: {1},<br /><br />Reason: {2}").format(helper.index+1, helper.text(), format(exc))
                )
                return
        # Check required cuts
        if self.functionType() in (tmGrammar.dist, tmGrammar.mass_inv, tmGrammar.mass_inv_3, tmGrammar.mass_trv):
            if len(self.selectedCuts()) < 1:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid expression"),
                    self.tr("Function {0}{{...}} requires at least one function cut.").format(self.functionType())
                )
                return
        # Validate whole expression
        try:
            self.validator.validate(AlgorithmFormatter.compress(self.expression()))
        except AlgorithmSyntaxError as exc:
            QtWidgets.QMessageBox.warning(
                self,
                self.tr("Invalid expression"),
                self.tr("Invalid expression: {0}").format(format(exc) or exc.token),
            )
            return
        super().accept()

# -----------------------------------------------------------------------------
#  Function requirement helper class
# -----------------------------------------------------------------------------

class FunctionReqHelper:

    def __init__(self, index, parent):
        self.index = index
        self.parent = parent
        self.label = QtWidgets.QLabel(parent.tr("Req. {0}").format(index + 1))
        self.lineEdit = QtWidgets.QLineEdit(parent)
        self.editButton = QtWidgets.QToolButton(parent)
        self.editButton.setText(parent.tr("..."))
        self.editButton.clicked.connect(self.edit)
        self.types = ObjectTypes # allowed object types

    def text(self):
        """Returns text of line edit."""
        return self.lineEdit.text()

    def isValid(self):
        """Retruns True if helper is enabled and contains input."""
        return self.lineEdit.isEnabled() and self.text()

    def setEnabled(self, enabled):
        self.label.setEnabled(enabled)
        self.lineEdit.setEnabled(enabled)
        self.editButton.setEnabled(enabled)

    def edit(self):
        dialog = ObjectEditorDialog(self.parent.menu, self.parent)
        dialog.setObjects(self.types)
        token = self.text()
        if token: # else start with empty editor
            try:
                dialog.loadObject(token)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(
                    self.parent,
                    self.parent.tr("Invalid expression"),
                    self.parent.tr("Invalid object expression: {0}").format(exc),
                )
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.lineEdit.setText(dialog.expression())
