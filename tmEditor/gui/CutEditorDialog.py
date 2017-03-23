# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Cut editor dialog.
"""

import tmGrammar

from tmEditor.core import toolbox
from tmEditor.core.Settings import CutSpecs

from tmEditor.core.Algorithm import Cut
from tmEditor.core.Algorithm import calculateDRRange
from tmEditor.core.Algorithm import calculateInvMassRange

# Common widgets
from tmEditor.gui.CommonWidgets import RestrictedLineEdit, ComboBoxPlus
from tmEditor.gui.CommonWidgets import EtaCutChart
from tmEditor.gui.CommonWidgets import PhiCutChart

from collections import namedtuple

import webbrowser
import re
import logging

from tmEditor.PyQt5Proxy import QtCore
from tmEditor.PyQt5Proxy import QtWidgets
from tmEditor.PyQt5Proxy import pyqt4_str

__all__ = ['CutEditorDialog', ]

# ------------------------------------------------------------------------------
#  Exceptions
# ------------------------------------------------------------------------------

class ValidationException(Exception):
    """Exeption for validation errors to be displayed in a message box."""
    def __init__(self, title, message):
        super(ValidationException, self).__init__(message)
        self.title = title

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kComment = 'comment'
kData = 'data'
kMaximum = 'maximum'
kMinimum = 'minimum'
kName = 'name'
kNumber = 'number'

# -----------------------------------------------------------------------------
#  Regular expressions
# -----------------------------------------------------------------------------

RegExFloatingPoint = re.compile(r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)')
"""Regular expression to match floating points."""

# -----------------------------------------------------------------------------
#  Scale spin box widgets
# -----------------------------------------------------------------------------

class ScaleSpinBox(QtWidgets.QDoubleSpinBox):
    """Custom spin box for scales lookup table."""

    MinimumMode = kMinimum
    MaximumMode = kMaximum
    EmptyScale = [{kNumber: 0, kMinimum: .0, kMaximum: .0}]

    def __init__(self, mode=MinimumMode, parent=None):
        super(ScaleSpinBox, self).__init__(parent)
        self.setMode(mode)
        self.setScale(self.EmptyScale)

    def reset(self):
        self.setScale(self.EmptyScale)

    def setMode(self, mode):
        self.mode = mode

    def setScale(self, scale, prec=3):
        """Scale requires a list of dictionaries with at least a *number*,
        *minimum* and *maximum* keys. *mode* specifies if the upper or lower bin
         limit is used."""
        # Important: sort the scale set by minimum or maximum - not by numbers (encoded in two's complement).
        self.scale = sorted(scale, key = lambda bin: float(bin[self.mode]))
        self.index = 0
        self.setDecimals(prec)
        minimum = min([float(value[self.mode]) for value in self.scale] or [0.])
        maximum = max([float(value[self.mode]) for value in self.scale] or [0.])
        self.setRange(minimum, maximum)

    def stepBy(self, steps):
        self.index += steps
        self.setValue(float(self.scale[self.index][self.mode]))

    def value(self, index=None):
        """Returns floating point value by bin index (upper or lower depending on mode)."""
        if index == None: index = self.index
        return float(self.scale[index][self.mode])

    def minimum(self):
        return self.value(0)

    def maximum(self):
        return self.value(-1)

    def setValue(self, value):
        value = self.nearest(value)
        super(ScaleSpinBox, self).setValue(value)

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        results = RegExFloatingPoint.findall(pyqt4_str(text))
        if results:
            return self.nearest(float(results[0]))

    def nearest(self, value):
        """Returns nearest neighbor of value in range."""
        # See also "finding index of an item closest to the value in a list that's not entirely sorted"
        # http://stackoverflow.com/questions/9706041/finding-index-of-an-item-closest-to-the-value-in-a-list-thats-not-entirely-sort
        result = min(range(len(self.scale)), key=lambda i: abs(float(self.scale[i][self.mode]) - float(value)))
        self.index = result
        return self.value(self.index)

# -----------------------------------------------------------------------------
#  Range spin box class
# -----------------------------------------------------------------------------

class RangeSpinBox(QtWidgets.QDoubleSpinBox):
    """Custom spin box for fixed stepped ranges."""

    def __init__(self, parent=None):
        super(RangeSpinBox, self).__init__(parent)

    def setMinimum(self, minimum):
        super(RangeSpinBox, self).setMinimum(self.nearest(minimum))

    def setMaximum(self, maximum):
        super(RangeSpinBox, self).setMaxnimum(self.nearest(maximum))

    def setRange(self, minimum, maximum):
        super(RangeSpinBox, self).setRange(self.nearest(minimum), self.nearest(maximum))

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        value, ok = QtCore.QLocale.system().toDouble(self.cleanText())
        return self.nearest(value)

    def nearest(self, value):
        """Returns nearest neighbor of value in range."""
        step = self.singleStep()
        return round(value / step) * step


# -----------------------------------------------------------------------------
#  Data field class
# -----------------------------------------------------------------------------

class DataField(QtWidgets.QScrollArea):
    """Custom data field for cuts.
    >>> d = DataField()
    >>> d.setEntries({"0": "foo", "1": "bar", "2": "baz"})
    >>> d.setData("0,2")
    >>> d.data()
    "0,2"
    """

    def __init__(self, parent = None):
        super(DataField, self).__init__(parent)
        self.clear()

    def setEntries(self, d, exclusive=False):
        """Provide a dictionary for data entries. If set exclusive the default
        check boxes are replaced by radio buttons."""
        self.clear()
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(self)
        for key, label in sorted(d.items(), key=toolbox.natural_sort_key):
            entry = QtWidgets.QRadioButton(label, self) if exclusive else QtWidgets.QCheckBox(label, self)
            entry.key = key
            self.entries.append(entry)
            layout.addWidget(entry)
        widget.setLayout(layout)
        self.setWidget(widget)

    def clear(self):
        """Clears all data entries."""
        widget = QtWidgets.QWidget(self)
        self.setWidget(widget)
        self.entries = []

    def data(self):
        """Returns comma separated list of enabled data entries."""
        indexes = []
        for entry in self.entries:
            if entry.isChecked():
                indexes.append(entry.key)
        return ','.join(indexes)

    def setData(self, data):
        """Sets data entries to supplied data. Data is a comma separated list."""
        # Convert from comma separated string list to list of integers.
        data = [index.strip() for index in data.split(',')] if data else []
        for key in data:
            for entry in self.entries:
                if key == entry.key:
                    entry.setChecked(True)

# -----------------------------------------------------------------------------
#  Cut editor dialog class
# -----------------------------------------------------------------------------

class CutEditorDialog(QtWidgets.QDialog):
    """Dialog providing cut creation/editing interface."""

    def __init__(self, menu, specs=None, parent=None):
        """Param title is the applciation name.
        Settings is a list of cut specification items."""
        super(CutEditorDialog, self).__init__(parent)
        # Attributes
        self.menu = menu
        self.specs = specs or CutSpecs
        self.loadedCut = None
        self.setupUi()
        self.reset()
        # HACK set whentrying to duplicate an item, this needs to be
        # implemented in a more decent way in future!
        self.copyMode = False

    def setupUi(self):
        # Dialog appeareance
        self.setWindowTitle(self.tr("Cut Editor"))
        self.resize(600, 400)
        # Cut type
        self.typeLabel = QtWidgets.QLabel(self.tr("Type"), self)
        self.typeComboBox = ComboBoxPlus(self)
        # Cut suffix
        self.suffixLineEdit = RestrictedLineEdit(self)
        self.suffixLineEdit.setRegexPattern('[a-zA-Z0-9_]+')
        self.suffixLabel = QtWidgets.QLabel(self.tr("Suffix"), self)
        # Initialize list of cut types
        self.loadCutTypes(self.specs)
        # Sizes
        unitLabelSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        # Minimum
        self.minimumLabel = QtWidgets.QLabel(self.tr("Minimum"), self)
        self.minimumSpinBox = ScaleSpinBox(ScaleSpinBox.MinimumMode, self)
        self.minimumSpinBox.valueChanged.connect(self.updateGraphs)
        self.minimumRangeSpinBox = RangeSpinBox(self)
        self.minimumUnitLabel = QtWidgets.QLabel(self)
        self.minimumUnitLabel.setSizePolicy(unitLabelSizePolicy)
        # Maximum
        self.maximumLabel = QtWidgets.QLabel(self.tr("Maximum"), self)
        self.maximumSpinBox = ScaleSpinBox(ScaleSpinBox.MaximumMode, self)
        self.maximumSpinBox.valueChanged.connect(self.updateGraphs)
        self.maximumRangeSpinBox = RangeSpinBox(self)
        self.maximumUnitLabel = QtWidgets.QLabel(self)
        self.maximumUnitLabel.setSizePolicy(unitLabelSizePolicy)
        # Infinite maximum option
        self.infiniteMaximumCheckBox = QtWidgets.QCheckBox(self.tr("infinite"), self)
        # Data
        self.dataLabel = QtWidgets.QLabel(self.tr("Data"), self)
        self.dataField = DataField(self)
        # Eta preview
        self.etaLabel = QtWidgets.QLabel(self.tr("Preview"), self)
        self.etaChart = EtaCutChart(self)
        # Phi preview
        self.phiLabel = QtWidgets.QLabel(self.tr("Preview"), self)
        self.phiChart = PhiCutChart(self)
        # Comment
        self.commentLabel = QtWidgets.QLabel(self.tr("Comment"), self)
        self.commentTextEdit = QtWidgets.QPlainTextEdit(self)
        self.commentTextEdit.setMaximumHeight(50)
        # Info box
        self.infoTextEdit = QtWidgets.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        # Button box
        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Help |
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.helpRequested.connect(self.showHelp)
        # Create layout.
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(self.typeLabel, 0, 0)
        gridLayout.addWidget(self.typeComboBox, 0, 1)
        gridLayout.addWidget(self.suffixLabel, 1, 0)
        gridLayout.addWidget(self.suffixLineEdit, 1, 1)
        gridLayout.addWidget(self.minimumLabel, 2, 0)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.minimumSpinBox)
        hbox.addWidget(self.minimumRangeSpinBox)
        hbox.addWidget(self.minimumUnitLabel)
        gridLayout.addLayout(hbox, 2, 1)
        gridLayout.addWidget(self.maximumLabel, 3, 0)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.maximumSpinBox)
        hbox.addWidget(self.maximumRangeSpinBox)
        hbox.addWidget(self.maximumUnitLabel)
        gridLayout.addLayout(hbox, 3, 1)
        gridLayout.addWidget(self.infiniteMaximumCheckBox, 4, 1)
        gridLayout.addWidget(self.etaLabel, 5, 0)
        gridLayout.addWidget(self.etaChart, 5, 1)
        gridLayout.addWidget(self.phiLabel, 6, 0)
        gridLayout.addWidget(self.phiChart, 6, 1)
        gridLayout.addWidget(self.dataLabel, 7, 0)
        gridLayout.addWidget(self.dataField, 7, 1)
        gridLayout.addWidget(self.commentLabel, 8, 0)
        gridLayout.addWidget(self.commentTextEdit, 8, 1, 1, 2)
        gridLayout.addWidget(self.infoTextEdit, 0, 2, 8, 1)
        gridLayout.addWidget(buttonBox, 9, 0, 1, 3)
        self.setLayout(gridLayout)
        # Setup connections.
        self.typeComboBox.currentIndexChanged.connect(self.updateEntries)

    def reset(self):
        self.typeComboBox.setCurrentIndex(0)
        self.suffixLineEdit.setText(self.tr("Unnamed"))
        self.updateEntries()

    def loadCutTypes(self, specs):
        """Load cut types from specifications."""
        # Populate cut types.
        self.typeComboBox.clear()
        for spec in specs:
            # Check if item is disabled: { enabled: false } [optional]
            if spec.enabled:
                self.typeComboBox.addItem(spec.name, spec)
                # on missing scale (editing outdated XML?)
                if spec.type in (tmGrammar.ETA, tmGrammar.PHI):
                    if spec.name not in self.menu.scales.bins:
                        self.typeComboBox.setItemEnabled(self.typeComboBox.count() - 1, False)

    @property
    def spec(self):
        return (CutSpecs.query(name=self.typename) or [None])[0]

    @property
    def name(self):
        return "{0}_{1}".format(self.typeComboBox.currentText(), self.suffixLineEdit.text())

    def setName(self, name):
        # TODO not nice...
        tokens = name.split('_')
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(tokens[0]))
        self.suffixLineEdit.setText('_'.join(tokens[1:]))

    @property
    def typename(self):
        return pyqt4_str(self.typeComboBox.currentText()) # PyQt4 safe

    @property
    def type(self):
        return self.spec.type

    @property
    def object(self):
        return self.spec.object

    @property
    def suffix(self):
        return pyqt4_str(self.suffixLineEdit.text())

    def setSuffix(self, text):
        self.suffixLineEdit.setText(text)

    @property
    def minimum(self):
        """Returns minimum in string representation."""
        if self.type in (tmGrammar.MASS, tmGrammar.DR, tmGrammar.DETA, tmGrammar.DPHI):
            return self.minimumRangeSpinBox.value()
        return self.minimumSpinBox.value()

    def setMinimum(self, value):
        """Set minimum value."""
        self.setRangeEnabled(True)
        self.minimumSpinBox.setValue(self.minimumSpinBox.nearest(value))
        self.minimumRangeSpinBox.setValue(float(value))

    @property
    def maximum(self):
        """Returns maximum in string representation."""
        if self.type in (tmGrammar.MASS, tmGrammar.DR, tmGrammar.DETA, tmGrammar.DPHI):
            return self.maximumRangeSpinBox.value()
        return self.maximumSpinBox.value()

    def setMaximum(self, value):
        """Set maximum value."""
        self.setRangeEnabled(True)
        self.maximumSpinBox.setValue(self.maximumSpinBox.nearest(value))
        self.maximumRangeSpinBox.setValue(float(value))

    @property
    def data(self):
        """Returns data string."""
        return self.dataField.data()

    def setData(self, data):
        self.setDataEnabled(True)
        self.dataField.setData(data)

    @property
    def comment(self):
        """Returns comment text."""
        return pyqt4_str(self.commentTextEdit.toPlainText())

    def setComment(self, text):
        """Set comment text."""
        self.commentTextEdit.setPlainText(text)

    def loadCut(self, cut):
        """Load data from existing cut object, prevents change of type."""
        # TODO not effective, re-write.
        self.loadedCut = cut
        self.typeComboBox.setEnabled(False)
        self.suffixLineEdit.setEnabled(not list(filter(lambda algorithm: cut.name in algorithm.cuts(), self.menu.algorithms)))
        self.setName(cut.name)
        self.updateEntries()
        if cut.type in (tmGrammar.ISO, tmGrammar.QLTY, tmGrammar.CHG, tmGrammar.CHGCOR):
            self.setDataEnabled(True)
            self.dataField.setEntries(self.spec.data, self.spec.data_exclusive)
            self.setData(cut.data)
        else:
            self.setRangeEnabled(True)
            if cut.type in (tmGrammar.MASS, tmGrammar.DR, tmGrammar.DETA, tmGrammar.DPHI):
                self.minimumRangeSpinBox.setValue(float(cut.minimum))
                self.maximumRangeSpinBox.setValue(float(cut.maximum))
                if self.maximumRangeSpinBox.value() >= self.maximumRangeSpinBox.maximum():
                    self.infiniteMaximumCheckBox.setChecked(True)
            else:
                scale = cut.scale(self.menu.scales)
                self.minimumSpinBox.setScale(scale)
                self.minimumSpinBox.setValue(self.minimumSpinBox.nearest(cut.minimum))
                self.maximumSpinBox.setScale(scale)
                self.maximumSpinBox.setValue(self.maximumSpinBox.nearest(cut.maximum))
        self.setComment(cut.comment)

    def updateCut(self, cut):
        """Update existing cut object with values from editor."""
        # TODO not effective, re-write.
        assert cut.type == self.type
        assert cut.object == self.object
        cut.name = self.name
        if cut.data:
            cut.minimum = ''
            cut.maximum = ''
            cut.data = self.data
        else:
            cut.minimum = self.minimum
            cut.maximum = self.maximum
            cut.data = ''
        cut.comment = self.comment

    def newCut(self):
        cut = Cut(
            name=self.name,
            type=self.type,
            object=self.object,
            comment=self.comment,
        )
        if self.data:
            cut.minimum = ''
            cut.maximum = ''
            cut.data = self.data
        else:
            cut.minimum = self.minimum
            cut.maximum = self.maximum
            cut.data = ''
        return cut

    def setRangeEnabled(self, enabled):
        """Set range inputs enabled, diables data input."""
        # Determine type of spin boxes
        mode = self.type in (tmGrammar.MASS, tmGrammar.DR, tmGrammar.DETA, tmGrammar.DPHI)
        infiniteMode = self.type == tmGrammar.MASS
        self.minimumLabel.setEnabled(enabled)
        self.minimumSpinBox.setEnabled(enabled and not mode)
        self.minimumRangeSpinBox.setEnabled(enabled and mode)
        self.maximumLabel.setEnabled(enabled)
        self.maximumSpinBox.setEnabled(enabled and not mode)
        self.maximumRangeSpinBox.setEnabled(enabled and mode)
        self.dataLabel.setEnabled(not enabled)
        self.dataField.setEnabled(not enabled)
        self.minimumLabel.setVisible(enabled)
        self.minimumSpinBox.setVisible(enabled and not mode)
        self.minimumRangeSpinBox.setVisible(enabled and mode)
        self.minimumUnitLabel.setVisible(enabled and bool(self.spec.range_unit))
        self.maximumLabel.setVisible(enabled)
        self.maximumSpinBox.setVisible(enabled and not mode)
        self.maximumRangeSpinBox.setVisible(enabled and mode)
        self.maximumRangeSpinBox.setEnabled(True)
        self.maximumUnitLabel.setVisible(enabled and bool(self.spec.range_unit))
        self.infiniteMaximumCheckBox.setVisible(infiniteMode)
        self.infiniteMaximumCheckBox.setChecked(False)
        self.dataLabel.setVisible(not enabled)
        self.dataField.setVisible(not enabled)
        self.minimumUnitLabel.setText(self.spec.range_unit)
        self.maximumUnitLabel.setText(self.spec.range_unit)

    def setDataEnabled(self, enabled):
        """Set data input enabled, diables range inputs."""
        self.setRangeEnabled(not enabled)

    def updateEntries(self):
        """Update entries according to selected cut type."""
        # TODO way to complicated implemetnation, split up in methods.

        # Reset entries
        self.minimumSpinBox.reset()
        self.maximumSpinBox.reset()
        self.dataField.clear()
        self.etaLabel.hide()
        self.etaChart.hide()
        self.phiLabel.hide()
        self.phiChart.hide()

        # Information
        info = []
        if self.spec.title:
            self.spec._filename = ""
            info.append(pyqt4_str(self.tr("<h3>{0}</h3>")).format(self.spec.title))
        if self.spec.description:
            info.append(pyqt4_str(self.tr("<p>{0}</p>")).format(self.spec.description))
        if self.spec.data:
            self.setDataEnabled(True)
            self.dataField.setEntries(self.spec.data, self.spec.data_exclusive)

        # Delta eta
        elif self.type == tmGrammar.DETA:
            self.setRangeEnabled(True)
            def isMuEta(scale): # filter
                return scale['object']==tmGrammar.MU and scale['type']==tmGrammar.ETA
            def isJetEta(scale): # filter
                return scale['object']==tmGrammar.JET and scale['type']==tmGrammar.ETA
            scaleMu = list(filter(isMuEta, self.menu.scales.scales))[0]
            scaleCalo = list(filter(isJetEta, self.menu.scales.scales))[0]
            scale = scaleMu if scaleMu[kMaximum] > scaleCalo[kMaximum] else scaleCalo
            minimum = 0.
            maximum = float(scale[kMaximum]) * 2.
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(0)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            info.append(pyqt4_str(self.tr("<p><strong>Valid range:</strong> [{0}, {1}]</p>")).format(minimum, 0, 'f', 3, maximum, 0, 'f', 3))
            info.append(pyqt4_str(self.tr("<p><strong>Step:</strong> {0}</p>")).format(self.spec.range_step, 0, 'f', self.spec.range_precision))

        # Delta phi
        elif self.type == tmGrammar.DPHI:
            self.setRangeEnabled(True)
            def isMuPhi(scale): # filter
                return scale['object']==tmGrammar.MU and scale['type']==tmGrammar.PHI
            scale = list(filter(isMuPhi, self.menu.scales.scales))[0]
            minimum = 0.
            maximum = float(scale[kMaximum]) # TODO
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(0)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            info.append(pyqt4_str(self.tr("<p><strong>Valid range:</strong> [{0}, {1}]</p>")).format(minimum, 0, 'f', 3, maximum, 0, 'f', 3))
            info.append(pyqt4_str(self.tr("<p><strong>Step:</strong> {0}</p>")).format(self.spec.range_step, 0, 'f', self.spec.range_precision))

        # Delta ranges
        elif self.type == tmGrammar.DR:
            self.setRangeEnabled(True)
            minimum, maximum = calculateDRRange()
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(minimum)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            info.append(pyqt4_str(self.tr("<p><strong>Valid range:</strong> [0, +&infin;)</p>")))
            info.append(pyqt4_str(self.tr("<p><strong>Step:</strong> {0}</p>")).format(self.spec.range_step, 0, 'f', self.spec.range_precision))

        # Invariant mass
        elif self.type == tmGrammar.MASS:
            self.setRangeEnabled(True)
            minimum, maximum = calculateInvMassRange()
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(minimum)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            # Infinite maximum option
            self.maximumRangeSpinBox.setEnabled(False)
            self.infiniteMaximumCheckBox.setChecked(True)
            def setInfiniteMaximum(state):
                self.maximumRangeSpinBox.setEnabled(not state)
                self.maximumRangeSpinBox.setValue(maximum)
            self.infiniteMaximumCheckBox.stateChanged.connect(setInfiniteMaximum)
            info.append(pyqt4_str(self.tr("<p><strong>Valid range:</strong> [0, +&infin;)</p>")))
            info.append(pyqt4_str(self.tr("<p><strong>Step:</strong> {0}</p>")).format(self.spec.range_step, 0, 'f', self.spec.range_precision))

        # All other ranges
        else:
            self.setRangeEnabled(True)
            scale = self.menu.scales.bins[self.typename]

            self.minimumSpinBox.setScale(scale)
            self.maximumSpinBox.setScale(scale)

            minimum = self.minimumSpinBox.minimum()
            maximum = self.maximumSpinBox.maximum()

            self.minimumSpinBox.setValue(minimum)
            self.maximumSpinBox.setValue(maximum)

            if self.type == tmGrammar.ETA:
                self.etaLabel.show()
                self.etaChart.show()
            if self.type == tmGrammar.PHI:
                self.phiLabel.show()
                self.phiChart.show()
            self.updateGraphs()

            info.append(pyqt4_str(self.tr("<p><strong>Valid range:</strong> [{0}, {1}]</p>")).format(minimum, 0, 'f', 3, maximum, 0, 'f', 3))
        if not self.typeComboBox.isEnabled():
            info.append(pyqt4_str(self.tr("<p><strong>Note:</strong> Changing an existing cut's type is not allowed.</p>")))
        self.infoTextEdit.setText("".join(info))

    def updateGraphs(self, value = None):
        if self.type == tmGrammar.ETA:
            self.etaChart.setRange(self.minimumSpinBox.value(), self.maximumSpinBox.value())
            self.etaChart.update()
        if self.type == tmGrammar.PHI:
            self.phiChart.setRange(self.minimumSpinBox.value(), self.maximumSpinBox.value())
            self.phiChart.update()

    def validateData(self):
        """Validate data input, raises a ValidationException on error."""
        if self.spec.data and not self.data:
            raise ValidationException(
                self.tr("No data"),
                self.tr("It is not possible to create a cut without assigning a data selection.")
            )

    def validateRange(self):
        """Validate ETA ranges to match minimum <= maximum, raises a ValidationException on error."""
        if self.type in (tmGrammar.MASS, tmGrammar.DR, tmGrammar.DETA, tmGrammar.ETA):
            if self.minimum > self.maximum:
                raise ValidationException(
                    self.tr("Invalid range"),
                    self.tr("For non-phi cuts a range must follow: minimum <= maximum.")
                )

    def validateSuffix(self):
        """Validate suffix, check for empty or duplicated name, raises a ValidationException on error."""
        # Empty suffix?
        if not len(self.suffix):
            raise ValidationException(
                self.tr("Missing suffix"),
                self.tr("No suffix is given. It must be at least one character in length.")
            )
        # Name already used?
        if self.name in [cut.name for cut in self.menu.cuts]:
            duplicates = list(filter(lambda cut: cut.name == self.name, self.menu.cuts))
            isConflict = (self.loadedCut and self.loadedCut in duplicates)
            if (self.copyMode and isConflict) or (not isConflict): # wired...
                raise ValidationException(
                    self.tr("Name already used"),
                    pyqt4_str(self.tr("Suffix \"{0}\" is already used with a cut of type \"{1}\".")).format(self.suffix, self.type)
                )

    def accept(self):
        """Perform consistency checks befor accepting changes."""
        try:
            self.validateData()
            self.validateRange()
            self.validateSuffix()
        except ValidationException as e:
            QtWidgets.QMessageBox.warning(self, e.title, e.message)
            return
        super(CutEditorDialog, self).accept()

    def showHelp(self):
        """Raise remote contents help."""
        webbrowser.open_new_tab("http://globaltrigger.hephy.at/upgrade/tme/userguide#create-cuts")
