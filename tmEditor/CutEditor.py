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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['CutEditorDialog', ]

# -----------------------------------------------------------------------------
#  Custom widgets
# -----------------------------------------------------------------------------

class ScaleSpinBox(QDoubleSpinBox):
    """Custom spin box for scales lookup table."""

    MinimumMode = 'minimum'
    MaximumMode = 'maximum'
    EmptyScale = [{'number': 0, 'minimum': .0, 'maximum': .0}]

    def __init__(self, mode = MinimumMode, parent = None):
        super(ScaleSpinBox, self).__init__(parent)
        self.setMode(mode)
        self.setScale(self.EmptyScale)

    def reset(self):
        self.setScale(self.EmptyScale)

    def setMode(self, mode):
        self.mode = mode

    def setScale(self, scale, prec = 3):
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

    def value(self, index = None):
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

class DataField(QScrollArea):
    """Custom data field for cuts.
    >>> d = DataField(['foo', 'bar', 'baz'])
    >>> d.setData("0,2")
    >>> d.data()
    "0,2"
    """

    def __init__(self, parent = None):
        super(DataField, self).__init__(parent)
        self.clear()

    def setEntries(self, labels, exclusive = False):
        """Labels require a sorted list data entry labels. The size determines
        the overall size of data entries assigned. If set exclusive the default
        chekc boxes are replaced by radio buttons."""
        self.clear()
        widget = QWidget(self)
        layout = QVBoxLayout(self)
        for label in labels:
            entry = QRadioButton(label, self) if exclusive else QCheckBox(label, self)
            self.entries.append(entry)
            layout.addWidget(entry)
        widget.setLayout(layout)
        self.setWidget(widget)

    def clear(self):
        """Clears all data entries."""
        widget = QWidget(self)
        self.setWidget(widget)
        self.entries = []

    def data(self):
        """Returns comma separated list of enabled data entries."""
        indexes = []
        for index, entry in enumerate(self.entries):
            if entry.isChecked():
                indexes.append(str(index))
        return ','.join(indexes)

    def setData(self, data):
        """Sets data entries to supplied data. Data is a comma separated list."""
        # Convert from comma separated string list to list of integers.
        data = [int(index) for index in data.split(',')] if data else []
        for index in data:
            if index < len(self.entries):
                self.entries[index].setChecked(True)

class CutEditorDialog(QDialog):
    """Dialog providing cut creation/editing interface."""

    CutSettings = Settings.cutSettings()

    def __init__(self, menu, parent = None):
        """Param title is the applciation name."""
        super(CutEditorDialog, self).__init__(parent)
        # Dialog appeareance
        self.setWindowTitle(self.tr("Cut Editor"))
        self.resize(600, 400)
        # Attributes
        self.menu = menu
        self.loadedCut = None
        # Cut type
        self.typeLabel = QLabel(self.tr("Type"), self)
        self.typeComboBox = QComboBox(self)
        # Cut suffix
        self.suffixLineEdit = QLineEdit(self)
        self.suffixLabel = QLabel(self.tr("Suffix"), self)
        # Populate cut types.
        for spec in self.CutSettings:
            # Check if item is disabled: { enabled: false } [optional]
            if spec.enabled:
                self.typeComboBox.addItem(spec.name, spec)
        # Sizes
        unitLabelSizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        # Minimum
        self.minimumLabel = QLabel(self.tr("Minimum"), self)
        self.minimumSpinBox = ScaleSpinBox(ScaleSpinBox.MinimumMode, self)
        self.minimumSpinBox.valueChanged.connect(self.updateGraphs)
        self.minimumRangeSpinBox = QDoubleSpinBox(self)
        self.minimumUnitLabel = QLabel(self)
        self.minimumUnitLabel.setSizePolicy(unitLabelSizePolicy)
        # Maximum
        self.maximumLabel = QLabel(self.tr("Maximum"), self)
        self.maximumSpinBox = ScaleSpinBox(ScaleSpinBox.MaximumMode, self)
        self.maximumSpinBox.valueChanged.connect(self.updateGraphs)
        self.maximumRangeSpinBox = QDoubleSpinBox(self)
        self.maximumUnitLabel = QLabel(self)
        self.maximumUnitLabel.setSizePolicy(unitLabelSizePolicy)
        # Data
        self.dataLabel = QLabel(self.tr("Data"), self)
        self.dataField = DataField(self)
        # Eta preview
        self.etaLabel = QLabel(self.tr("Preview"), self)
        self.etaChart = EtaCutChart(self)
        # Phi preview
        self.phiLabel = QLabel(self.tr("Preview"), self)
        self.phiChart = PhiCutChart(self)
        # Comment
        self.commentLabel = QLabel(self.tr("Comment"), self)
        self.commentTextEdit = QPlainTextEdit(self)
        self.commentTextEdit.setMaximumHeight(50)
        # Info box
        self.infoTextEdit = QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        # Button box
        buttonBox = QDialogButtonBox(QDialogButtonBox.Help | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.helpRequested.connect(self.showHelp)
        # Create layout.
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.typeLabel, 0, 0)
        gridLayout.addWidget(self.typeComboBox, 0, 1)
        gridLayout.addWidget(self.suffixLabel, 1, 0)
        gridLayout.addWidget(self.suffixLineEdit, 1, 1)
        gridLayout.addWidget(self.minimumLabel, 2, 0)
        hbox = QHBoxLayout()
        hbox.addWidget(self.minimumSpinBox)
        hbox.addWidget(self.minimumRangeSpinBox)
        hbox.addWidget(self.minimumUnitLabel)
        gridLayout.addLayout(hbox, 2, 1)
        gridLayout.addWidget(self.maximumLabel, 3, 0)
        hbox = QHBoxLayout()
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
        # Setup contents.
        self.reset()

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
            self.dataField.setEntries(self.spec.data_sorted, self.spec.data_exclusive)
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
        if 'comment' in cut.keys():
            self.setComment(cut['comment'])

    def updateCut(self, cut):
        """Update existing cut object with values from editor."""
        # TODO not effective, re-write.
        assert cut.type == self.type
        assert cut.object == self.object
        cut['name'] = self.name
        if cut['data']:
            cut['minimum'] = ''
            cut['maximum'] = ''
            cut['data'] = self.data
        else:
            cut['minimum'] = self.minimum
            cut['maximum'] = self.maximum
            cut['data'] = ''
        cut['comment'] = self.comment

    def newCut(self):
        cut = Cut(
            name=self.name,
            type=self.type,
            object=self.object,
            comment=self.comment,
        )
        if self.data:
            cut['minimum'] = ''
            cut['maximum'] = ''
            cut['data'] = self.data
        else:
            cut['minimum'] = self.minimum
            cut['maximum'] = self.maximum
            cut['data'] = ''
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
        info = []
        if self.spec.title:
            self.spec._filename = ""
            info.append("<h3>{self.spec.title}</h3>".format(**locals()))
        if self.spec.description:
            info.append("<p>{self.spec.description}</p>".format(**locals()))
        if self.spec.data:
            self.setDataEnabled(True)
            self.dataField.setEntries(self.spec.data_sorted, self.spec.data_exclusive)
        # Delta ranges
        elif self.type == tmGrammar.DR:
            self.setRangeEnabled(True)
            self.minimumRangeSpinBox.setRange(0, 10E10)
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setValue(0)
            self.maximumRangeSpinBox.setRange(0, 10E10)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setValue(1.)
        elif self.type == tmGrammar.DETA:
            self.setRangeEnabled(True)
            scaleMu = filter(lambda scale: scale['object']==tmGrammar.MU and scale['type']==tmGrammar.ETA, self.menu.scales.scales)[0]
            scaleCalo = filter(lambda scale: scale['object']==tmGrammar.JET and scale['type']==tmGrammar.ETA, self.menu.scales.scales)[0]
            scale = scaleMu if scaleMu['maximum'] > scaleCalo['maximum'] else scaleCalo
            minimum, maximum = float(scale['minimum']), float(scale['maximum'])
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(0)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            minimum, maximum = self.minimumRangeSpinBox.minimum(), self.maximumRangeSpinBox.maximum()
            info.append("<p><strong>Valid range:</strong> [{minimum:.3f}, {maximum:.3f}]</p>".format(**locals()))
        elif self.type == tmGrammar.DPHI:
            self.setRangeEnabled(True)
            scale = filter(lambda scale: scale['object']==tmGrammar.MU and scale['type']==tmGrammar.PHI, self.menu.scales.scales)[0]
            minimum, maximum = float(scale['minimum']), float(scale['maximum']) / 2.
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.minimumRangeSpinBox.setRange(minimum, maximum)
            self.minimumRangeSpinBox.setValue(0)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(minimum, maximum)
            self.maximumRangeSpinBox.setValue(maximum)
            minimum, maximum = self.minimumRangeSpinBox.minimum(), self.maximumRangeSpinBox.maximum()
            info.append("<p><strong>Valid range:</strong> [{minimum:.3f}, {maximum:.3f}]</p>".format(**locals()))
        # Invariant mass
        elif self.type == tmGrammar.MASS:
            self.setRangeEnabled(True)
            self.minimumRangeSpinBox.setRange(0, 10E10)
            self.minimumRangeSpinBox.setValue(0)
            self.minimumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.minimumRangeSpinBox.setSingleStep(self.spec.range_step)
            self.maximumRangeSpinBox.setRange(0, 10E10)
            self.maximumRangeSpinBox.setValue(0)
            self.maximumRangeSpinBox.setDecimals(self.spec.range_precision)
            self.maximumRangeSpinBox.setSingleStep(self.spec.range_step)
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

            info.append("<p><strong>Valid range:</strong> [{minimum:.3f}, {maximum:.3f}]</p>".format(**locals()))
        if not self.typeComboBox.isEnabled():
            info.append("<p><strong>Note:</strong> Changing an existing cut's type is not allowed.</p>")
        self.infoTextEdit.setText("\n".join(info))

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
            QMessageBox.warning(
                self,
                self.tr("No data"),
                self.tr("It is not possible to create a cut without assigning a data selection.")
            )
            return
        # For all ranges (excepting PHI) minimum <= maximum
        if self.type in (tmGrammar.MASS, tmGrammar.DR, tmGrammar.DETA, tmGrammar.ETA):
            if float(self.minimum) > float(self.maximum):
                QMessageBox.warning(
                    self,
                    self.tr("Invalid range"),
                    self.tr("For non-phi cuts a range must follow: minimum <= maximum.")
                )
                return
        # Name already used?
        if self.name in [cut.name for cut in self.menu.cuts]:
            duplicates = filter(lambda cut: cut.name == self.name, self.menu.cuts)
            if not (self.loadedCut and self.loadedCut in duplicates): # ugly...
                QMessageBox.warning(
                    self,
                    self.tr("Name already used"),
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
    app = QApplication(sys.argv)
    menu = Menu(sys.argv[1])
    window = CutEditorDialog(menu)
    window.show()
    sys.exit(app.exec_())
