"""Bottom widget."""

import re
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

import tmGrammar

from tmEditor.core import formatter
from tmEditor.core.Settings import CutSpecs
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.types import FunctionTypes, CountObjectTypes, FunctionCutTypes

# Common widgets
from tmEditor.gui.CommonWidgets import IconLabel
from tmEditor.gui.CommonWidgets import EtaCutChart
from tmEditor.gui.CommonWidgets import PhiCutChart
from tmEditor.gui.CommonWidgets import richTextObjectsPreview
from tmEditor.gui.CommonWidgets import richTextSignalsPreview
from tmEditor.gui.CommonWidgets import richTextExtSignalsPreview
from tmEditor.gui.CommonWidgets import richTextCutsPreview
from tmEditor.gui.CommonWidgets import createIcon

from tmEditor import tmeditor_rc

__all__ = ['BottomWidget', ]

# HACK: overload with missing attributes.
tmGrammar.ET = "ET"
tmGrammar.PT = "PT"

kCable = 'cable'
kChannel = 'channel'
kDescription = 'description'
kLabel = 'label'
kMaximum = 'maximum'
kMinimum = 'minimum'
kNBits = 'n_bits'
kName = 'name'
kNumber = 'number'
kObject = 'object'
kStep = 'step'
kSystem = 'system'
kType = 'type'

# ------------------------------------------------------------------------------
#  Helpers
# ------------------------------------------------------------------------------

def highlight(expression):
    """Simple rich text highlighter for algorithm expressions."""
    expression = AlgorithmFormatter.normalize(expression)
    for name in FunctionTypes:
        expression = re.sub(
            r'({0})({{)'.format(name),
            r'<span style="color: blue; font-weight: bold;">\1</span>\2',
            expression
        )
    for name in (tmGrammar.AND, tmGrammar.OR, tmGrammar.XOR, tmGrammar.NOT):
        expression = re.sub(
            r'([\ \)])({0})([\ \(])'.format(name),
            r'\1<span style="color: darkblue; font-weight: bold;">\2</span>\3',
            expression
        )
    return expression

def fPatchType(item):
    """Patch muon type from ET to PT."""
    if item[kType] == tmGrammar.ET:
        if item[kObject] == tmGrammar.MU:
            return tmGrammar.PT
    return item[kType]

# ------------------------------------------------------------------------------
#  Toolbar widget, helper
# ------------------------------------------------------------------------------

class ToolbarWidget(QtWidgets.QWidget):

    addTriggered = QtCore.pyqtSignal()
    editTriggered = QtCore.pyqtSignal()
    copyTriggered = QtCore.pyqtSignal()
    removeTriggered = QtCore.pyqtSignal()
    moveTriggered = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.addButton = QtWidgets.QPushButton(createIcon("list-add"), self.tr("Add..."), self)
        self.addButton.clicked.connect(lambda: self.addTriggered.emit())
        layout.addWidget(self.addButton)
        layout.addStretch(10)
        self.editButton = QtWidgets.QPushButton(createIcon("text-editor"), self.tr("Edit..."), self)
        self.editButton.clicked.connect(lambda: self.editTriggered.emit())
        layout.addWidget(self.editButton)
        self.copyButton = QtWidgets.QPushButton(createIcon("edit-copy"), self.tr("Copy..."), self)
        self.copyButton.clicked.connect(lambda: self.copyTriggered.emit())
        layout.addWidget(self.copyButton)
        self.removeButton = QtWidgets.QPushButton(createIcon("list-remove"), self.tr("Remove"), self)
        self.removeButton.clicked.connect(lambda: self.removeTriggered.emit())
        layout.addWidget(self.removeButton)
        self.moveButton = QtWidgets.QPushButton(createIcon("select-index"), self.tr("Move"), self)
        self.moveButton.clicked.connect(lambda: self.moveTriggered.emit())
        layout.addWidget(self.moveButton)
        self.setLayout(layout)
        self.setAutoFillBackground(True)

    def setButtonsEnabled(self, enabled):
        self.editButton.setEnabled(enabled)
        self.copyButton.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)
        self.moveButton.setEnabled(enabled)

# ------------------------------------------------------------------------------
#  Bottom preview widget
# ------------------------------------------------------------------------------

class BottomWidget(QtWidgets.QWidget):
    """Widget displayed below table view showing previews of selected items."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.toolbar = ToolbarWidget(self)
        self.notice = IconLabel(QtGui.QIcon(), "", self)
        self.notice.setAutoFillBackground(True)
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("BottomWidgetTextEdit")
        self.textEdit.setStyleSheet("""
        #BottomWidgetTextEdit {
            border: 0;
            background-color: #eee;
        }""")

        self.etaCutChart = EtaCutChart(self)
        # MacOS workaround, need to wrap group box to avoid layout glitch
        self.etaCutWidget = QtWidgets.QWidget(self)
        self.etaCutWidget.setObjectName("etaCutWidget")
        self.etaCutWidget.setStyleSheet("""
        #etaCutWidget {
            background-color: #eee;
        }""")
        # Group box
        groupBox = QtWidgets.QGroupBox(self.tr("Eta preview"), self)
        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.etaCutChart)
        groupBox.setLayout(box)
        groupBox.setAlignment(QtCore.Qt.AlignBottom)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(groupBox)
        self.etaCutWidget.setLayout(layout)

        self.phiCutChart = PhiCutChart(self)
        # MacOS workaround, need to wrap group box to avoid layout glitch
        self.phiCutWidget = QtWidgets.QWidget(self)
        self.phiCutWidget.setObjectName("phiCutWidget")
        self.phiCutWidget.setStyleSheet("""
        #phiCutWidget {
            background-color: #eee;
        }""")
        # Group box
        groupBox = QtWidgets.QGroupBox(self.tr("Phi preview"), self)
        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.phiCutChart)
        groupBox.setLayout(box)
        groupBox.setAlignment(QtCore.Qt.AlignBottom)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(groupBox)
        self.phiCutWidget.setLayout(layout)

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar, 0, 0, 1, 3)
        layout.addWidget(self.notice, 1, 0, 1, 3)
        layout.addWidget(self.textEdit, 2, 0)
        layout.addWidget(self.etaCutWidget, 2, 1)
        layout.addWidget(self.phiCutWidget, 2, 2)
        self.setLayout(layout)
        self.reset()

    def reset(self) -> None:
        self.clearNotice()
        self.etaCutWidget.hide()
        self.phiCutWidget.hide()
        self.clearNotice()

    def setNotice(self, text: str, icon: Optional[QtGui.QIcon] = None) -> None:
        self.notice.show()
        self.notice.iconLabel.hide()
        self.notice.iconLabel.clear()
        self.notice.setText(text)
        if icon:
            self.notice.iconLabel.show()
            self.notice.setIcon(icon)

    def clearNotice(self) -> None:
        self.notice.hide()
        self.notice.setText("")
        self.notice.iconLabel.clear()

    def setEtaCutChart(self, lower, upper):
        self.etaCutChart.setRange(lower, upper)
        self.etaCutWidget.show()

    def setPhiCutChart(self, lower, upper):
        self.phiCutChart.setRange(lower, upper)
        self.phiCutWidget.show()

    def setText(self, message: str) -> None:
        self.textEdit.setText(message)

    # Load params from item

    def loadAlgorithm(self, algorithm, menu):
        self.reset()
        # Format expression
        content = []
        content.append(self.tr("<h2><span>{}</span> {}</h2>").format(algorithm.index, algorithm.name))
        content.append(self.tr("<p><strong>Expression:</strong></p>"))
        content.append(self.tr("<p><code>{}</code></p>").format(highlight(algorithm.expression)))
        if algorithm.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>{}</code></p>").format(algorithm.comment))
        content.append(richTextObjectsPreview(algorithm, self))
        content.append(richTextSignalsPreview(algorithm, self))
        content.append(richTextExtSignalsPreview(algorithm, self))
        content.append(richTextCutsPreview(menu, algorithm, self))
        self.setText("".join(content))

    def loadCut(self, cut):
        self.reset()
        content = []
        content.append(self.tr("<h2>{}</h2>").format(cut.name))
        if cut.type not in FunctionCutTypes:
            content.append(self.tr("<p><strong>Object:</strong> {}</p>").format(cut.object))
        if cut.data:
            datalist = []
            # TODO HACK transitional backward compatibility
            if cut.type == tmGrammar.SLICE:
                if cut.data:
                    cut.minimum = float(cut.data.split(",")[0].strip())
                    cut.maximum = float(cut.data.split(",")[-1].strip())
                if cut.minimum == cut.maximum:
                    data = "[{}]".format(int(cut.minimum))
                else:
                    data = "[{}-{}]".format(int(cut.minimum), int(cut.maximum))
                content.append(self.tr("<p><strong>Range:</strong> {}</p>".format(data)))
            else:
                content.append(self.tr("<p><strong>Options:</strong></p>"))
                if cut.type == tmGrammar.CHGCOR: # HACK
                    data_ = CutSpecs.query(type=cut.type)[0].data # TODO
                else:
                    data_ = CutSpecs.query(type=cut.type, object=cut.object)[0].data # TODO
                for key in cut.data.split(','):
                    if cut.type == tmGrammar.ISO:
                        datalist.append(self.tr("<li>[0b{0:02b}] {1}</li>").format(int(key), data_[key]))
                    else:
                        datalist.append(self.tr("<li>[{}] {}</li>").format(key, data_[key]))
                content.append(self.tr("<p><ul>{}</ul></p>").format("".join(datalist)))
        elif cut.type == tmGrammar.TBPT:
            content.append(self.tr("<p><strong>Threshold:</strong> {}</p>").format(formatter.fCutValue(cut.minimum)))
        else:
            content.append(self.tr("<p><strong>Minimum:</strong> {}</p>").format(formatter.fCutValue(cut.minimum)))
            content.append(self.tr("<p><strong>Maximum:</strong> {}</p>").format(formatter.fCutValue(cut.maximum)))
        if cut.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>{}</code></p>").format(cut.comment))
        self.setText("".join(content))
        # Show charts if available.
        if cut.type == tmGrammar.ETA:
            self.setEtaCutChart(float(cut.minimum), float(cut.maximum))
        elif cut.type == tmGrammar.PHI:
            self.setPhiCutChart(float(cut.minimum), float(cut.maximum))

    def loadObject(self, obj):
        self.reset()
        content = []
        content.append(self.tr("<h2>{}</h2>").format(obj.name))
        content.append(self.tr("<p><strong>Type:</strong> {}</p>").format(obj.type))
        if obj.type in CountObjectTypes:
            content.append(self.tr("<p><strong>Threshold:</strong> {} {}</p>").format(formatter.fComparison(obj.comparison_operator), formatter.fCounts(obj.threshold)))
        else:
            content.append(self.tr("<p><strong>Threshold:</strong> {} {}</p>").format(formatter.fComparison(obj.comparison_operator), formatter.fThreshold(obj.threshold)))
        content.append(self.tr("<p><strong>BX offset:</strong> {}</p>").format(formatter.fBxOffset(obj.bx_offset)))
        if obj.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>{}</code></p>").format(obj.comment))
        self.setText("".join(content))

    def loadExternal(self, menu, external):
        self.reset()
        content = []
        content.append(self.tr("<h2>{}</h2>").format(external.name))
        content.append(self.tr("<p><strong>BX offset:</strong> {}</p>").format(formatter.fBxOffset(external.bx_offset)))
        data = list(filter(lambda item: item[kName] == external.signal_name, menu.extSignals.extSignals))[0]
        content.append(self.tr("<p><strong>System:</strong> {}</p>").format(data[kSystem]))
        if kLabel in data.keys():
            content.append(self.tr("<p><strong>Label:</strong> {}</p>").format(data[kLabel]))
        content.append(self.tr("<p><strong>Cable:</strong> {}</p>").format(data[kCable]))
        content.append(self.tr("<p><strong>Channel:</strong> {}</p>").format(data[kChannel]))
        if kDescription in data.keys():
            content.append(self.tr("<p><strong>Description:</strong> {}</p>").format(data[kDescription]))
        if external.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>{}</code></p>").format(external.comment))
        self.setText("".join(content))

    def loadScale(self, data): # TODO
        self.reset()
        content = []
        content.append(self.tr("<p><strong>Object:</strong> {}</p>").format(data[kObject]))
        content.append(self.tr("<p><strong>Type:</strong> {}</p>").format(fPatchType(data)))
        content.append(self.tr("<p><strong>Minimum:</strong> {}</p>").format(formatter.fCutValue(data[kMinimum])))
        content.append(self.tr("<p><strong>Maximum:</strong> {}</p>").format(formatter.fCutValue(data[kMaximum])))
        content.append(self.tr("<p><strong>Step:</strong> {}</p>").format(formatter.fCutValue(data[kStep])))
        content.append(self.tr("<p><strong>Bitwidth:</strong> {}</p>").format(data[kNBits]))
        self.setText("".join(content))

    def loadScaleType(self, name, data): # TODO
        self.reset()
        content = []
        content.append(self.tr("<h2>Scale {}</h2>").format(name))
        content.append(self.tr("<p><strong>Number:</strong> {}</p>").format(data[kNumber]))
        content.append(self.tr("<p><strong>Minimum:</strong> {}</p>").format(formatter.fCutValue(data[kMinimum])))
        content.append(self.tr("<p><strong>Maximum:</strong> {}</p>").format(formatter.fCutValue(data[kMaximum])))
        self.setText("".join(content))

    def loadSignal(self, data): # TODO
        self.reset()
        content = []
        content.append(self.tr("<h2>{}</h2>").format(data[kName]))
        content.append(self.tr("<p><strong>System:</strong> {}</p>").format(data[kSystem]))
        content.append(self.tr("<p><strong>Name:</strong> {}</p>").format(data[kName]))
        if kLabel in data.keys():
            content.append(self.tr("<p><strong>Label:</strong> {}</p>").format(data[kLabel]))
        content.append(self.tr("<p><strong>Cable:</strong> {}</p>").format(data[kCable]))
        content.append(self.tr("<p><strong>Channel:</strong> {}</p>").format(data[kChannel]))
        if kDescription in data.keys():
            content.append(self.tr("<p><strong>Description:</strong> {}</p>").format(data[kDescription]))
        self.setText("".join(content))
