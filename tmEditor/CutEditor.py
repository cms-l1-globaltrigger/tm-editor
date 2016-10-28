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
    Settings,
)
from tmEditor.CommonWidgets import (
    EtaCutChart,
    PhiCutChart,
)
from tmEditor.Menu import Cut
import tmGrammar
from collections import namedtuple

import webbrowser
import re, math, logging

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['CutEditorDialog', ]

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
#  Custom widgets
# -----------------------------------------------------------------------------

class ScaleSpinBox(QtGui.QDoubleSpinBox):
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
        """Returns bins floating point value by LUT index (upper or lower depending on mode)."""
        if index == None: index = self.index
        return self.scale[index][self.mode]

    def minimum(self):
        return float(self.value(0))

    def maximum(self):
        return float(self.value(-1))

    def setValue(self, value):
        value = self.nearest(value)
        super(ScaleSpinBox, self).setValue(value)

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        return self.nearest(float(str(text).strip(" =<>!")))

    def nearest(self, value):
        """Returns nearest neighbor of value in range."""
        # See also "finding index of an item closest to the value in a list that's not entirely sorted"
        # http://stackoverflow.com/questions/9706041/finding-index-of-an-item-closest-to-the-value-in-a-list-thats-not-entirely-sort
        result = min(range(len(self.scale)), key = lambda i: abs(float(self.scale[i][self.mode]) - float(value)))
        self.index = result
        return float(self.value(self.index))

class RangeSpinBox(QtGui.QDoubleSpinBox):
    """Custom spin box for fixed stepped ranges."""

    def __init__(self, parent=None):
        super(RangeSpinBox, self).__init__(parent)

    def stepBy(self, steps):
        self.setValue(self.value() + (steps * self.singleStep()))

    def setValue(self, value):
        value = self.nearest(value)
        super(RangeSpinBox, self).setValue(value)

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        return self.nearest(float(str(text).strip(" =<>!")))

    def nearest(self, value):
        """Returns nearest neighbor of value in range."""
        # Calculate modulo of value by multiplying by 10^decimals
        multiplier = int(10**self.decimals())
        value = int(round(value * multiplier))
        step = int(round(self.singleStep() * multiplier))
        value = (value / step) * step # mangle
        return float(value) / multiplier

class DataField(QtGui.QScrollArea):
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
        widget = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout(self)
        for key, label in sorted(d.iteritems(), key=Toolbox.natural_sort_key):
            entry = QtGui.QRadioButton(label, self) if exclusive else QtGui.QCheckBox(label, self)
            entry.key = key
            self.entries.append(entry)
            layout.addWidget(entry)
        widget.setLayout(layout)
        self.setWidget(widget)

    def clear(self):
        """Clears all data entries."""
        widget = QtGui.QWidget(self)
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

class CutEditorDialog(QtGui.QDialog):
    """Dialog providing cut creation/editing interface."""

    CutSettings = Settings.cutSettings

    def __init__(self, menu, parent = None):
        """Param title is the applciation name."""
        super(CutEditorDialog, self).__init__(parent)
        # Attributes
        self.menu = menu
        self.loadedCut = None
        self.setupUi()
        self.reset()

    def setupUi(self):
        # Dialog appeareance
        self.setWindowTitle(self.tr("Cut Editor"))
        self.resize(600, 400)
        # Cut type
        self.typeLabel = QtGui.QLabel(self.tr("Type"), self)
        self.typeComboBox = QtGui.QComboBox(self)
        # Cut suffix
        self.suffixLineEdit = QtGui.QLineEdit(self)
        self.suffixLabel = QtGui.QLabel(self.tr("Suffix"), self)
        # Populate cut types.
        for spec in self.CutSettings:
            # Check if item is disabled: { enabled: false } [optional]
            if spec.enabled:
                self.typeComboBox.addItem(spec.name, spec)
        # Sizes
        unitLabelSizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        # Minimum
        self.minimumLabel = QtGui.QLabel(self.tr("Minimum"), self)
        self.minimumSpinBox = ScaleSpinBox(ScaleSpinBox.MinimumMode, self)
        self.minimumSpinBox.valueChanged.connect(self.updateGraphs)
        self.minimumRangeSpinBox = RangeSpinBox(self)
        self.minimumUnitLabel = QtGui.QLabel(self)
        self.minimumUnitLabel.setSizePolicy(unitLabelSizePolicy)
        # Maximum
        self.maximumLabel = QtGui.QLabel(self.tr("Maximum"), self)
        self.maximumSpinBox = ScaleSpinBox(ScaleSpinBox.MaximumMode, self)
        self.maximumSpinBox.valueChanged.connect(self.updateGraphs)
        self.maximumRangeSpinBox = RangeSpinBox(self)
        self.maximumUnitLabel = QtGui.QLabel(self)
        self.maximumUnitLabel.setSizePolicy(unitLabelSizePolicy)
        # Data
        self.dataLabel = QtGui.QLabel(self.tr("Data"), self)
        self.dataField = DataField(self)
        # Eta preview
        self.etaLabel = QtGui.QLabel(self.tr("Preview"), self)
        self.etaChart = EtaCutChart(self)
        # Phi preview
        self.phiLabel = QtGui.QLabel(self.tr("Preview"), self)
        self.phiChart = PhiCutChart(self)
        # Comment
        self.commentLabel = QtGui.QLabel(self.tr("Comment"), self)
        self.commentTextEdit = QtGui.QPlainTextEdit(self)
        self.commentTextEdit.setMaximumHeight(50)
        # Info box
        self.infoTextEdit = QtGui.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        # Button box
        buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Help |
            QtGui.QDialogButtonBox.Ok |
            QtGui.QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.helpRequested.connect(self.showHelp)
        # Create layout.
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.typeLabel, 0, 0)
        gridLayout.addWidget(self.typeComboBox, 0, 1)
        gridLayout.addWidget(self.suffixLabel, 1, 0)
        gridLayout.addWidget(self.suffixLineEdit, 1, 1)
        gridLayout.addWidget(self.minimumLabel, 2, 0)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.minimumSpinBox)
        hbox.addWidget(self.minimumRangeSpinBox)
        hbox.addWidget(self.minimumUnitLabel)
        gridLayout.addLayout(hbox, 2, 1)
        gridLayout.addWidget(self.maximumLabel, 3, 0)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.maximumSpinBox)
        hbox.addWidget(self.maximumRangeSpinBox)
        hbox.addWidget(self.maximumUnitLabel)
        gridLayout.addLayout(hbox, 3, 1)
        gridLayout.addWidget(self.etaLabel, 4, 0)
        gridLayout.addWidget(self.etaChart, 4, 1)
        gridLayout.addWidget(self.phiLabel, 5, 0)
        gridLayout.addWidget(self.phiChart, 5, 1)
        gridLayout.addWidget(self.dataLabel, 6, 0)
        gridLayout.addWidget(self.dataField, 6, 1)
        gridLayout.addWidget(self.commentLabel, 7, 0)
        gridLayout.addWidget(self.commentTextEdit, 7, 1, 1, 2)
        gridLayout.addWidget(self.infoTextEdit, 0, 2, 7, 1)
        gridLayout.addWidget(buttonBox, 8, 0, 1, 3)
        self.setLayout(gridLayout)
        # Setup connections.
        self.typeComboBox.currentIndexChanged.connect(self.updateEntries)

    def reset(self):
        self.typeComboBox.setCurrentIndex(0)
        self.suffixLineEdit.setText(self.tr("Unnamed"))
        self.updateEntries()

    @property
    def spec(self):
        return filter(lambda spec: spec.name == self.typename, self.CutSettings)[0]

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
        return str(self.typeComboBox.currentText())

    @property
    def type(self):
        return self.spec.type

    @property
    def object(self):
        return self.spec.object

    @property
    def suffix(self):
        return str(self.suffixLineEdit.text())

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
        return str(self.commentTextEdit.toPlainText())

    def setComment(self, text):
        """Set comment text."""
        self.commentTextEdit.setPlainText(text)

    def loadCut(self, cut):
        """Load data from existing cut object, prevents change of type."""
        # TODO not effective, re-write.
        self.loadedCut = cut
        self.typeComboBox.setEnabled(False)
        self.suffixLineEdit.setEnabled(not filter(lambda algorithm: cut.name in algorithm.cuts(), self.menu.algorithms))
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
            else:
                scale = cut.scale(self.menu.scales)
                self.minimumSpinBox.setScale(scale)
                self.minimumSpinBox.setValue(float(self.minimumSpinBox.nearest(cut.minimum)))
                self.maximumSpinBox.setScale(scale)
                self.maximumSpinBox.setValue(float(self.maximumSpinBox.nearest(cut.maximum)))
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
        self.maximumUnitLabel.setVisible(enabled and bool(self.spec.range_unit))
        self.dataLabel.setVisible(not enabled)
        self.dataField.setVisible(not enabled)
        self.minimumUnitLabel.setText(self.spec.range_unit)
        self.maximumUnitLabel.setText(self.spec.range_unit)

    def setDataEnabled(self, enabled):
        """Set data input enabled, diables range inputs."""
        self.setRangeEnabled(not enabled)

    def updateEntries(self):
        """Update entries according to selected cut type."""
        # TODO not effective, re-write.
        self.minimumSpinBox.reset()
        self.maximumSpinBox.reset()
        self.dataField.clear()
        self.etaLabel.hide()
        self.etaChart.hide()
        self.phiLabel.hide()
        self.phiChart.hide()
        info = QtCore.QStringList()
        if self.spec.title:
            self.spec._filename = ""
            info.append(self.tr("<h3>%1</h3>").arg(self.spec.title))
        if self.spec.description:
            info.append(self.tr("<p>%1</p>").arg(self.spec.description))
        if self.spec.data:
            self.setDataEnabled(True)
            self.dataField.setEntries(self.spec.data, self.spec.data_exclusive)
        # Delta ranges
        elif self.type == tmGrammar.DR:
            self.setRangeEnabled(True)
            minimum, maximum = 0., 10E10 # TODO TODO
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(minimum)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(1.)
            info.append(self.tr("<p><strong>Valid range:</strong> [0, +&infin;)</p>"))
            info.append(self.tr("<p><strong>Step:</strong> %1</p>").arg(self.spec.range_step, 0, 'f', self.spec.range_precision))
        elif self.type == tmGrammar.DETA:
            self.setRangeEnabled(True)
            def isMuEta(scale): # filter
                return scale['object']==tmGrammar.MU and scale['type']==tmGrammar.ETA
            def isJetEta(scale): # filter
                return scale['object']==tmGrammar.JET and scale['type']==tmGrammar.ETA
            scaleMu = filter(isMuEta, self.menu.scales.scales)[0]
            scaleCalo = filter(isJetEta, self.menu.scales.scales)[0]
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
            info.append(self.tr("<p><strong>Valid range:</strong> [%1, %2]</p>").arg(minimum, 0, 'f', 3).arg(maximum, 0, 'f', 3))
            info.append(self.tr("<p><strong>Step:</strong> %1</p>").arg(self.spec.range_step, 0, 'f', self.spec.range_precision))
        elif self.type == tmGrammar.DPHI:
            self.setRangeEnabled(True)
            def isMuPhi(scale): # filter
                return scale['object']==tmGrammar.MU and scale['type']==tmGrammar.PHI
            scale = filter(isMuPhi, self.menu.scales.scales)[0]
            minimum = 0.
            maximum = float(scale[kMaximum]) / 2. # TODO confirm max DPHI range!
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(0)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            info.append(self.tr("<p><strong>Valid range:</strong> [%1, %2]</p>").arg(minimum, 0, 'f', 3).arg(maximum, 0, 'f', 3))
            info.append(self.tr("<p><strong>Step:</strong> %1</p>").arg(self.spec.range_step, 0, 'f', self.spec.range_precision))
        # Invariant mass
        elif self.type == tmGrammar.MASS:
            self.setRangeEnabled(True)
            minimum = 0.
            maximum = 10E10 # TODO TODO
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(minimum)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            info.append(self.tr("<p><strong>Valid range:</strong> [0, +&infin;)</p>"))
            info.append(self.tr("<p><strong>Step:</strong> %1</p>").arg(self.spec.range_step, 0, 'f', self.spec.range_precision))
        # Ranges
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

            info.append(self.tr("<p><strong>Valid range:</strong> [%1, %2]</p>").arg(minimum, 0, 'f', 3).arg(maximum, 0, 'f', 3))
        if not self.typeComboBox.isEnabled():
            info.append(self.tr("<p><strong>Note:</strong> Changing an existing cut's type is not allowed.</p>"))
        self.infoTextEdit.setText(info.join(""))

    def updateGraphs(self, value = None):
        if self.type == tmGrammar.ETA:
            self.etaChart.setRange(float(self.minimumSpinBox.value()), float(self.maximumSpinBox.value()))
            self.etaChart.update()
        if self.type == tmGrammar.PHI:
            self.phiChart.setRange(float(self.minimumSpinBox.value()), float(self.maximumSpinBox.value()))
            self.phiChart.update()

    def accept(self):
        """Perform consistency checks befor accepting changes."""
        if self.spec.data and not self.data:
            QtGui.QMessageBox.warning(self, self.tr("No data"),
                self.tr("It is not possible to create a cut without assigning a data selection.")
            )
            return
        # For all ranges (excepting PHI) minimum <= maximum
        if self.type in (tmGrammar.MASS, tmGrammar.DR, tmGrammar.DETA, tmGrammar.ETA):
            if float(self.minimum) > float(self.maximum):
                QtGui.QMessageBox.warning(self, self.tr("Invalid range"),
                    self.tr("For non-phi cuts a range must follow: minimum <= maximum.")
                )
                return
        # Name already used?
        if self.name in [cut.name for cut in self.menu.cuts]:
            duplicates = filter(lambda cut: cut.name == self.name, self.menu.cuts)
            if not (self.loadedCut and self.loadedCut in duplicates): # ugly...
                QtGui.QMessageBox.warning(self, self.tr("Name already used"),
                    self.tr("Suffix \"%1\" is already used with a cut of type \"%2\".").arg(self.suffix).arg(self.type)
                )
                return
        super(CutEditorDialog, self).accept()

    def showHelp(self):
        """Raise remote contents help."""
        webbrowser.open_new_tab("http://globaltrigger.hephy.at/upgrade/tme/userguide#create-cuts")

if __name__ == '__main__':
    import sys
    from tmEditor import Menu
    app = QtGui.QApplication(sys.argv)
    menu = Menu(sys.argv[1])
    window = CutEditorDialog(menu)
    window.show()
    sys.exit(app.exec_())
