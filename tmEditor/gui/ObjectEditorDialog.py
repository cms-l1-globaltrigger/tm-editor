"""Object editor dialog."""
from typing import Iterable, List, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

import tmGrammar

from tmEditor.core.Settings import CutSpecs
from tmEditor.core.formatter import fCutLabel
from tmEditor.core.types import ThresholdObjectTypes
from tmEditor.core.types import CountObjectTypes
from tmEditor.core.types import ObjectTypes
from tmEditor.core.types import SignalTypes

from tmEditor.core.Algorithm import toObject, objectCuts
from tmEditor.core.AlgorithmHelper import AlgorithmHelper
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter

# Common widgets
from tmEditor.gui.CommonWidgets import PrefixedSpinBox
from tmEditor.gui.CommonWidgets import TextFilterWidget
from tmEditor.gui.CommonWidgets import ComboBoxPlus
from tmEditor.gui.CommonWidgets import createIcon, miniIcon

from tmEditor.gui.CutEditorDialog import CutEditorDialog

__all__ = ["ObjectEditorDialog"]

# -----------------------------------------------------------------------------
#  Keys
# -----------------------------------------------------------------------------

kMinimum = "minimum"
kMaximum = "maximum"
kObject = "object"
kStep = "step"
kType = "type"
kET = "ET"
kCOUNT = "COUNT"
kCicadaPrecScaleType = "CICADA-CICADA-CscoreValues"

# -----------------------------------------------------------------------------
#  Object capabilites
# -----------------------------------------------------------------------------

ThresholdType = "threshold"
CounterType = "counter"
SignalType = "signal"

ObjectCapabilities = {
    ThresholdType: {"scales": True, "threshold": True},
    CounterType: {"scales": True, "threshold": False},
    SignalType: {"scales": False, "threshold": False},
}

ExtendedTypes = ObjectTypes + SignalTypes

def getObjectType(objectType):
    if objectType in ThresholdObjectTypes:
        return ThresholdType
    if objectType in CountObjectTypes:
        return ThresholdType
    if objectType in SignalTypes:
        return SignalType
    return None

def getObjectCapabilities(objectType):
    return ObjectCapabilities.get(getObjectType(objectType))

# -----------------------------------------------------------------------------
#  Cut item class
# -----------------------------------------------------------------------------

class CutItem(QtGui.QStandardItem):
    """A checkable cut standard item, to be inserted to a list model."""

    def __init__(self, text, checked=False):
        super().__init__(text)
        self.setEditable(False)
        self.setCheckable(True)
        if checked:
            self.setCheckState(QtCore.Qt.Checked)

# -----------------------------------------------------------------------------
#  Object editor dialog class
# -----------------------------------------------------------------------------

class ObjectEditorDialog(QtWidgets.QDialog):
    """Object editor dialog class."""

    def __init__(self, menu: object, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """Constructor, takes a reference to a menu and an optional parent.
        """
        super().__init__(parent)
        self.setMenu(menu)
        self.setObjectTypes(list(ExtendedTypes))
        self.setupUi()
        self.initObjectList(self.objectTypes())
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
        self.compareComboBox.addItem(">=", tmGrammar.GE)
        self.compareComboBox.addItem("==", tmGrammar.EQ)

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

        layout = QtWidgets.QGridLayout(self)
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

    def menu(self) -> object:
        return self._menu

    def setMenu(self, menu: object) -> None:
        self._menu = menu

    def objectTypes(self) -> List:
        return self._objectTypes

    def setObjectTypes(self, types: Iterable) -> None:
        self._objectTypes = list(types)

    def updateObjectType(self):
        """Update inputs according to selected object type."""

        import logging

        objectType = self.objectType()
        objectCapabilities = getObjectCapabilities(objectType)
        if objectCapabilities.get("threshold"):
            self.compareComboBox.setVisible(True)
            self.thresholdSpinBox.setVisible(True)
        else:
            self.compareComboBox.setVisible(False)
            self.thresholdSpinBox.setVisible(False)
        if objectCapabilities.get("scales"):
            scale = self.getScale(objectType)
            # Just to make sure...
            if scale is None:
                QtWidgets.QMessageBox.critical(
                    self,
                    self.tr("Failed to load scales"),
                    self.tr("Missing scales for object of type {0}").format(objectType),
                )
                return
            self.thresholdSpinBox.setRange(float(scale[kMinimum]), float(scale[kMaximum]))
            self.thresholdSpinBox.setSingleStep(float(scale[kStep]))
        else:
            self.thresholdSpinBox.setRange(0, 0)
        if objectType in ThresholdObjectTypes:
            self.thresholdSpinBox.setSuffix(" GeV")
            self.thresholdSpinBox.setDecimals(1)
        elif objectType in CountObjectTypes:
            self.thresholdSpinBox.setDecimals(0)
            self.thresholdSpinBox.setSuffix("")
        self.updateInfoText()
        self.initCuts()
        # Toggle cut creation button (disable if no cuts available for object type).
        specs = CutSpecs.query(object=self.objectType())
        self.addCutButton.setEnabled(len(specs))

    def initObjectList(self, objects):
        """Initialize list of available objects. Ignores objects with no scales."""
        for index, name in enumerate(ExtendedTypes):
            if name not in objects:
                continue # ignore if not in init list
            self.typeComboBox.addItem(miniIcon(name.lower()), name)                
            if name in ObjectTypes:
                if not self.getScale(name): # on missing scale (editing outdated XML?)
                    self.typeComboBox.setItemEnabled(index, False)
            if name == tmGrammar.CICADA:
                if not self.getPrecScale(kCicadaPrecScaleType):
                    self.typeComboBox.setItemEnabled(index, False)             

    def initCuts(self):
        """Initialize list of checkable cuts."""
        self.cutModel = QtGui.QStandardItemModel(self)
        self.cutModel._items = []
        for cut in sorted(self.menu().cuts, key=lambda cut: cut.name):
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
        scales = list(filter(lambda item: item[kObject] == objectType, self.menu().scales.scales))
        # Get only threshold/count scales
        return (list(filter(lambda item: item[kType] in (kET, kCOUNT, ), scales)) or [None])[0]

    def getPrecScale(self, scaleType):
        """Returns scale for object or None if not found."""
        # Get only scales of object type
        scales = list(filter(lambda item: item[kObject] == "PRECISION", self.menu().scales.scales))
        # Get only threshold/count scales
        return (list(filter(lambda item: item[kType] in (scaleType), scales)) or [None])[0]

    def updateFilter(self, text):
        """Update cut filter."""
        self.cutListView.model().setFilterWildcard(text)

    def objectType(self) -> str:
        """Returns object type."""
        return self.typeComboBox.currentText()

    def comparisonOperator(self) -> Optional[str]:
        """Returns comparison operator."""
        return self.compareComboBox.itemData(self.compareComboBox.currentIndex())

    def threshold(self):
        """Returns objects threshold."""
        return self.thresholdSpinBox.value()

    def bxOffset(self):
        return self.offsetSpinBox.value()

    def selectedCuts(self) -> List[str]:
        """Retruns list of checked cut names."""
        return [item.data().name for item in list(filter(lambda item: item.checkState() == QtCore.Qt.Checked, self.cutModel._items))]

    def expression(self):
        """Returns object expression selected by the inputs."""
        expression = AlgorithmHelper()
        if self.objectType() in SignalTypes:
            expression.addSignal(
                type=self.objectType(),
                bx_offset=self.bxOffset(),
                cuts=self.selectedCuts(),
            )
        else:
            expression.addObject(
                type=self.objectType(),
                comparison_operator=self.comparisonOperator(),
                threshold=self.threshold(),
                bx_offset=self.bxOffset(),
                cuts=self.selectedCuts(),
            )
        return AlgorithmFormatter.normalize(expression.serialize())

    def updateInfoText(self):
        """Update info box text."""
        objectType = self.objectType()
        objectCapabilities = getObjectCapabilities(objectType)
        text = []
        text.append(f"<h3>{objectType} Object Requirement</h3>")
        if objectCapabilities.get("scales"):
            scale = self.getScale(objectType)
            minimum = float(scale[kMinimum])
            maximum = float(scale[kMaximum])
            step = float(scale[kStep])
            if objectType in ThresholdObjectTypes:
                text.append(f"<p>Valid threshold: {minimum:.1f} GeV - {maximum:.1f} GeV ({step:.1f} GeV steps)</p>")
            elif objectType in CountObjectTypes:
                text.append(f"<p>Valid count: {minimum:.0f} - {maximum:.0f}</p>")
        expression = self.expression()
        text.append(f"<h4>Preview</h4>")
        text.append(f"<p><pre>{expression}</pre></p>")
        self.infoTextEdit.setText("".join(text))

    def loadObject(self, token):
        """Load dialog by values from object. Will raise a ValueError if string
        *token* is not a valid object.
        """
        object_ = toObject(token)
        if object_.type not in self.objectTypes():
            raise ValueError("Invalid object type.")
        object_.cuts = objectCuts(token)
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(object_.type))
        self.compareComboBox.setCurrentIndex(self.compareComboBox.findData(object_.comparison_operator))
        self.thresholdSpinBox.setValue(object_.decodeThreshold())
        self.offsetSpinBox.setValue(object_.bx_offset)
        for cut in self.cutModel._items:
            if cut.data().name in object_.cuts:
                cut.setCheckState(QtCore.Qt.Checked)

    def addCut(self):
        """Raise cut editor to add a new cut."""
        # Load cut settings only for selected object type
        dialog = CutEditorDialog(self.menu(), self)
        specs = CutSpecs.query(object=self.objectType())
        dialog.setupCuts(specs)
        dialog.setModal(True)
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        new_cut = dialog.newCut()
        self.menu().addCut(new_cut)
        # TODO code refactoring!
        # Restore selected cuts and newly added one.
        selectedCuts = self.selectedCuts()
        self.initCuts()
        # TODO code refactoring!
        # Restore selected cuts and newly added one.
        for cut in self.cutModel._items:
            if cut.data().name in selectedCuts:
                cut.setCheckState(QtCore.Qt.Checked)
            # Select newly added cut
            if cut.data().name == new_cut.name:
                cut.setCheckState(QtCore.Qt.Checked)
