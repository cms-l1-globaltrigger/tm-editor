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
)
import tmGrammar
from collections import namedtuple
import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['CutEditorDialog', ]

FunctionCutObjects = {
    'MASS': 'MASS',
    'DR': 'DIST',
    'DETA': 'DIST',
    'DPHI': 'DIST',
    'CHGCOR': 'COMB',
}

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
        minimum = min([float(value[self.mode]) for value in self.scale])
        maximum = max([float(value[self.mode]) for value in self.scale])
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

    def setEntries(self, labels):
        """labels requires a sorted list data entry labels. The size determines
        the overall size of data entries assigned."""
        self.clear()
        widget = QWidget(self)
        layout = QVBoxLayout(self)
        for label in labels:
            checkBox = QCheckBox(label, self)
            # checkBox.setToolTip()
            self.checkBoxes.append(checkBox)
            layout.addWidget(checkBox)
        widget.setLayout(layout)
        self.setWidget(widget)

    def clear(self):
        """Clears all data entries."""
        widget = QWidget(self)
        self.setWidget(widget)
        self.checkBoxes = []

    def data(self):
        """Returns comma separated list of enabled data entries."""
        indexes = []
        for index, checkBox in enumerate(self.checkBoxes):
            if checkBox.isChecked():
                indexes.append(str(index))
        return ','.join(indexes)

    def setData(self, data):
        """Sets data entries to supplied data. Data is a comma separated list."""
        # Convert from comma separated string list to list of integers.
        data = [int(index) for index in data.split(',')] if data else []
        for index in data:
            if index < len(self.checkBoxes):
                self.checkBoxes[index].setChecked(True)

class CutEditorDialog(QDialog):
    """Dialog providing cut creation/editing interface."""

    CutSettings = Toolbox.Settings['cuts']

    def __init__(self, menu, parent = None):
        """Param title is the applciation name, version the main applications
        version."""
        super(CutEditorDialog, self).__init__(parent)
        # Dialog appeareance
        self.setWindowTitle(self.tr("Cut Editor"))
        self.resize(600, 400)
        # Attributes
        self.menu = menu
        # Cut type
        self.typeLabel = QLabel(self.tr("Type"), self)
        self.typeComboBox = QComboBox(self)
        # Cut suffix
        self.suffixLineEdit = QLineEdit(self)
        self.suffixLabel = QLabel(self.tr("Suffix"), self)
        # Populate cut types.
        for item in self.CutSettings:
            # Check if item is disabled: { enabled: false } [optional]
            if 'enabled' in item.keys():
                if not item['enabled']:
                    continue
            self.typeComboBox.addItem(item['name'], item)
        # Minimum
        self.minimumLabel = QLabel(self.tr("Minimum"), self)
        #self.minimumSpinBox = QComboBox(self)#QDoubleSpinBox(self)
        self.minimumSpinBox = ScaleSpinBox(ScaleSpinBox.MinimumMode, self)
        # Maximum
        self.maximumLabel = QLabel(self.tr("Maximum"), self)
        #self.maximumSpinBox = QComboBox(self)#QDoubleSpinBox(self)
        self.maximumSpinBox = ScaleSpinBox(ScaleSpinBox.MaximumMode, self)
        # Data
        self.dataLabel = QLabel(self.tr("Data"), self)
        self.dataField = DataField(self)
        # Comment
        self.commentLabel = QLabel(self.tr("Comment"), self)
        self.commentTextEdit = QPlainTextEdit(self)
        self.commentTextEdit.setMaximumHeight(50)
        # Info box
        self.infoTextEdit = QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        # Button box
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        # Create layout.
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.typeLabel, 0, 0)
        gridLayout.addWidget(self.typeComboBox, 0, 1)
        gridLayout.addWidget(self.suffixLabel, 1, 0)
        gridLayout.addWidget(self.suffixLineEdit, 1, 1)
        gridLayout.addWidget(self.minimumLabel, 2, 0)
        gridLayout.addWidget(self.minimumSpinBox, 2, 1)
        gridLayout.addWidget(self.maximumLabel, 3, 0)
        gridLayout.addWidget(self.maximumSpinBox, 3, 1)
        gridLayout.addWidget(self.dataLabel, 4, 0)
        gridLayout.addWidget(self.dataField, 4, 1)
        gridLayout.addWidget(self.commentLabel, 5, 0)
        gridLayout.addWidget(self.commentTextEdit, 5, 1, 1, 2)
        gridLayout.addWidget(self.infoTextEdit, 0, 2, 5, 1)
        gridLayout.addWidget(buttonBox, 6, 0, 1, 3)
        self.setLayout(gridLayout)
        # Setup connections.
        self.typeComboBox.currentIndexChanged.connect(self.updateEntries)
        # Setup contents.
        self.reset()

    def reset(self):
        self.typeComboBox.setCurrentIndex(0)
        self.suffixLineEdit.setText(self.tr("Unnamed"))
        self.updateEntries()

    def name(self):
        return "{0}_{1}".format(self.typeComboBox.currentText(), self.suffixLineEdit.text())

    def setName(self, name):
        # TODO not nice...
        tokens = name.split('_')
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(tokens[0]))
        self.suffixLineEdit.setText('_'.join(tokens[1:]))

    def type(self):
        """Returns type name."""
        return self.getCurrentCutSettings()['type']

    def object(self):
        """Returns object name."""
        return self.getCurrentCutSettings()['object']

    def suffix(self):
        """Returns suffix."""
        return str(self.suffixLineEdit.text())

    def minimum(self):
        """Returns minimum floating point string or None if not a range type cut."""
        if 'data' in self.getCurrentCutSettings().keys():
            return None
        #return self.minimumSpinBox.itemData(self.minimumSpinBox.currentIndex()).toPyObject()['minimum']
        return self.minimumSpinBox.value()

    def setMinimum(self, value):
        self.setRangeEnabled(True)
        self.minimumSpinBox.setValue(float(self.minimumSpinBox.nearest(value)))
        #self.minimumSpinBox.setCurrentIndex(self.minimumSpinBox.findText(format(float(value), "+.3f")))

    def maximum(self):
        """Returns maximum floating point string or None if not a range type cut."""
        if 'data' in self.getCurrentCutSettings().keys():
            return None
        #return self.maximumSpinBox.itemData(self.maximumSpinBox.currentIndex()).toPyObject()['maximum']
        return self.maximumSpinBox.value()

    def data(self):
        """Returns data string or None if not a data type cut."""
        if not 'data' in self.getCurrentCutSettings().keys():
            return None
        #return str(self.dataField.itemData(self.dataField.currentIndex()).toPyObject()) # retuns dict key (lookup index)
        return self.dataField.data()

    def setData(self, data):
        self.setDataEnabled(True)
        #self.dataField.setCurrentIndex(int(data))
        self.dataField.setData(data)

    def comment(self):
        """Returns comment text."""
        return str(self.commentTextEdit.toPlainText())

    def setComment(self, text):
        """Set comment text."""
        self.commentTextEdit.setPlainText(text)

    def loadCut(self, cut):
        """Load data from existing cut object, prevents change of type."""
        # TODO not effective, re-write.
        self.typeComboBox.setEnabled(False)
        self.setName(cut.name)
        self.updateEntries()
        if cut.type in ('ISO', 'QLTY', 'CHGCOR'):
            self.setDataEnabled(True)
            labels = self.getCurrentCutSettings()['data']
            labels = [labels[str(k)] for k in sorted([int(i) for i in labels.keys()])]
            self.dataField.setEntries(labels)
            self.setData(cut.data)
        else:
            self.setRangeEnabled(True)
            self.minimumSpinBox.setScale(cut.scale(self.menu.scales))
            self.minimumSpinBox.setValue(float(self.minimumSpinBox.nearest(cut.minimum)))
            self.maximumSpinBox.setScale(cut.scale(self.menu.scales))
            self.maximumSpinBox.setValue(float(self.maximumSpinBox.nearest(cut.maximum)))
        if 'comment' in cut.keys():
            self.commentTextEdit.setPlainText(cut['comment'])

    def updateCut(self, cut):
        """Update existing cut object with values from editor."""
        # TODO not effective, re-write.
        assert cut.type == self.type()
        assert cut.object == self.object()
        cut['name'] = self.name()
        cut['minimum'] = self.minimum() or ''
        cut['maximum'] = self.maximum() or ''
        cut['data'] = self.data() or ''
        cut['comment'] = str(self.commentTextEdit.toPlainText())

    def setRangeEnabled(self, enabled):
        """Set range inputs enabled, diables data input."""
        self.minimumLabel.setEnabled(enabled)
        self.minimumSpinBox.setEnabled(enabled)
        self.maximumLabel.setEnabled(enabled)
        self.maximumSpinBox.setEnabled(enabled)
        self.dataLabel.setEnabled(not enabled)
        self.dataField.setEnabled(not enabled)
        self.minimumLabel.setVisible(enabled)
        self.minimumSpinBox.setVisible(enabled)
        self.maximumLabel.setVisible(enabled)
        self.maximumSpinBox.setVisible(enabled)
        self.dataLabel.setVisible(not enabled)
        self.dataField.setVisible(not enabled)

    def setDataEnabled(self, enabled):
        """Set data input enabled, diables range inputs."""
        self.setRangeEnabled(not enabled)

    def getCurrentCutSettings(self):
        """Retruns dict holding settings for current selected cut."""
        name = str(self.typeComboBox.currentText())
        return filter(lambda item: item['name'] == name, self.CutSettings)[0]

    def updateEntries(self):
        # TODO not effective, re-write.
        item = self.getCurrentCutSettings()
        self.infoTextEdit.clear()
        info = []
        if 'title' in item.keys():
            info.append("<h3><img src=\"/usr/share/icons/gnome/16x16/actions/help-about.png\"/> {title}</h3>".format(**item))
        if 'description' in item.keys():
            info.append("<p>{description}</p>".format(**item))
        if 'data' in item.keys():
            self.setDataEnabled(True)
            #self.dataField.clear()
            # brrrr.... >_<'
            #for key in [str(i) for i in sorted([int(key) for key in item['data'].keys()])]:
            #    self.dataField.addItem(item['data'][key], key)
            keys = sorted([int(key) for key in item['data'].keys()])
            labels = [item['data'][str(k)] for k in keys]
            self.dataField.setEntries(labels)
        elif self.type() in ('DR', 'DETA', 'DPHI', 'MASS'):
            self.dataField.clear()
        else:
            self.setRangeEnabled(True)
            typename = str('-'.join((item['object'], item['type']))) # TODO: Recast to string required (why?)

            print "typename:",  typename
            scale = self.menu.scales.bins[typename]


            self.minimumSpinBox.setScale(scale)
            self.maximumSpinBox.setScale(scale)

            self.minimumSpinBox.setValue(self.minimumSpinBox.minimum())
            self.maximumSpinBox.setValue(self.maximumSpinBox.maximum())

            self.dataField.clear()
            minimum = self.minimumSpinBox.minimum()
            maximum = self.maximumSpinBox.maximum()
            info.append("<p><strong>Valid range:</strong> [{minimum:.3f}, {maximum:.3f}]</p>".format(**locals()))
        if not self.typeComboBox.isEnabled():
            info.append("<p><strong>Note:</strong> Changing an existing cut's type is not allowed.</p>".format(**item))
        self.infoTextEdit.setText("".join(info))
