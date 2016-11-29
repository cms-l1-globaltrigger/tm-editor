# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

import tmGrammar

from tmEditor.core import Toolbox
from tmEditor.core import Settings
from tmEditor.core.Algorithm import toObject
from tmEditor.core.Types import CountObjectTypes

# Common widgets
from tmEditor.gui.CommonWidgets import IconLabel
from tmEditor.gui.CommonWidgets import EtaCutChart
from tmEditor.gui.CommonWidgets import PhiCutChart
from tmEditor.gui.CommonWidgets import richTextObjectsPreview
from tmEditor.gui.CommonWidgets import richTextExtSignalsPreview
from tmEditor.gui.CommonWidgets import richTextCutsPreview

from PyQt4 import QtCore
from PyQt4 import QtGui

import re

from tmEditor import tmeditor_rc

__all__ = ['BottomWidget', ]

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
    expression = Toolbox.fAlgorithm(expression)
    for name in (tmGrammar.comb, tmGrammar.dist, tmGrammar.mass):
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

# ------------------------------------------------------------------------------
#  Toolbar widget, helper
# ------------------------------------------------------------------------------

class ToolbarWidget(QtGui.QWidget):

    addTriggered = QtCore.pyqtSignal()
    editTriggered = QtCore.pyqtSignal()
    copyTriggered = QtCore.pyqtSignal()
    removeTriggered = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ToolbarWidget, self).__init__(parent)
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.addButton = QtGui.QPushButton(Toolbox.createIcon("list-add"), self.tr("Add..."), self)
        self.addButton.clicked.connect(lambda: self.addTriggered.emit())
        layout.addWidget(self.addButton)
        layout.addStretch(10)
        self.editButton = QtGui.QPushButton(Toolbox.createIcon("text-editor"), self.tr("Edit..."), self)
        self.editButton.clicked.connect(lambda: self.editTriggered.emit())
        layout.addWidget(self.editButton)
        self.copyButton = QtGui.QPushButton(Toolbox.createIcon("edit-copy"), self.tr("Copy..."), self)
        self.copyButton.clicked.connect(lambda: self.copyTriggered.emit())
        layout.addWidget(self.copyButton)
        self.removeButton = QtGui.QPushButton(Toolbox.createIcon("list-remove"), self.tr("Remove"), self)
        self.removeButton.clicked.connect(lambda: self.removeTriggered.emit())
        layout.addWidget(self.removeButton)
        self.setLayout(layout)
        self.setAutoFillBackground(True)

    def setButtonsEnabled(self, enabled):
        self.editButton.setEnabled(enabled)
        self.copyButton.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)

# ------------------------------------------------------------------------------
#  Bottom preview widget
# ------------------------------------------------------------------------------

class BottomWidget(QtGui.QWidget):
    """Widget displayed below table view showing previews of selected items."""

    def __init__(self, parent=None):
        super(BottomWidget, self).__init__(parent)
        self.toolbar = ToolbarWidget(self)
        self.notice = IconLabel(QtGui.QIcon(), QtCore.QString(), self)
        self.notice.setAutoFillBackground(True)
        self.textEdit = QtGui.QTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("BottomWidgetTextEdit")
        self.textEdit.setStyleSheet("""
        #BottomWidgetTextEdit {
            border: 0;
            background-color: #eee;
        }""")

        self.EtaCutChart = EtaCutChart(self)
        self.EtaCutChartBox = QtGui.QGroupBox(self.tr("Eta preview"), self)
        box = QtGui.QVBoxLayout()
        box.addWidget(self.EtaCutChart)
        self.EtaCutChartBox.setLayout(box)
        self.EtaCutChartBox.setAlignment(QtCore.Qt.AlignTop)
        self.EtaCutChartBox.setObjectName("EtaCutChartBox")
        self.EtaCutChartBox.setStyleSheet("""
        #EtaCutChartBox {
            background-color: #eee;
        }""")

        self.PhiCutChart = PhiCutChart(self)
        self.PhiCutChartBox = QtGui.QGroupBox(self.tr("Phi preview"), self)
        box = QtGui.QVBoxLayout()
        box.addWidget(self.PhiCutChart)
        self.PhiCutChartBox.setLayout(box)
        self.PhiCutChartBox.setAlignment(QtCore.Qt.AlignTop)
        self.PhiCutChartBox.setObjectName("PhiCutChartBox")
        self.PhiCutChartBox.setStyleSheet("""
        #PhiCutChartBox {
            background-color: #eee;
        }""")

        layout = QtGui.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar, 0, 0, 1, 3)
        layout.addWidget(self.notice, 1, 0, 1, 3)
        layout.addWidget(self.textEdit, 2, 0)
        layout.addWidget(self.EtaCutChartBox, 2, 1)
        layout.addWidget(self.PhiCutChartBox, 2, 2)
        self.setLayout(layout)
        self.reset()

    def reset(self):
        self.clearNotice()
        self.EtaCutChartBox.hide()
        self.PhiCutChartBox.hide()
        self.clearNotice()

    def setNotice(self, text, icon=None):
        self.notice.show()
        self.notice.icon.hide()
        self.notice.icon.clear()
        self.notice.setText(text)
        if icon:
            self.notice.icon.show()
            self.notice.setIcon(icon)

    def clearNotice(self):
        self.notice.hide()
        self.notice.setText("")
        self.notice.icon.clear()
        self.notice.label.clear()

    def setEtaCutChart(self, lower, upper):
        self.EtaCutChart.setRange(lower, upper)
        self.EtaCutChartBox.show()

    def setPhiCutChart(self, lower, upper):
        self.PhiCutChart.setRange(lower, upper)
        self.PhiCutChartBox.show()

    def setText(self, message):
        self.textEdit.setText(message)

    # Load params from item

    def loadAlgorithm(self, algorithm, menu):
        self.reset()
        # Format expression
        content = QtCore.QStringList()
        content.append(self.tr("<h2>%1 %2</h2>").arg(algorithm.index).arg(algorithm.name))
        content.append(self.tr("<p><strong>Expression:</strong></p>"))
        content.append(self.tr("<p><code>%1</code></p>").arg(highlight(algorithm.expression)))
        if algorithm.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>%1</code></p>").arg(algorithm.comment))
        content.append(richTextObjectsPreview(algorithm, self))
        content.append(richTextExtSignalsPreview(algorithm, self))
        content.append(richTextCutsPreview(menu, algorithm, self))
        self.setText(content.join(""))

    def loadCut(self, cut):
        self.reset()
        content = QtCore.QStringList()
        content.append(self.tr("<h2>%1</h2>").arg(cut.name))
        content.append(self.tr("<p><strong>Type:</strong> %1</p>").arg(cut.object))
        if cut.data:
            content.append(self.tr("<p><strong>Data:</strong></p>"))
            if cut.object == tmGrammar.comb: # TODO TODO TODO
                typename = cut.type
            else:
                typename = '-'.join((cut.object, cut.type)) # '<object>-<type>'
            data_ = filter(lambda entry: entry.name == typename, Settings.CutSettings)[0].data # TODO
            datalist = QtCore.QStringList()
            for key in cut.data.split(','):
                datalist.append(self.tr("<li>[%1] %2</li>").arg(key).arg(data_[key]))
            content.append(self.tr("<p><ul>%1</ul></p>").arg(datalist.join("")))
        else:
            content.append(self.tr("<p><strong>Minimum:</strong> %1</p>").arg(Toolbox.fCut(cut.minimum)))
            content.append(self.tr("<p><strong>Maximum:</strong> %1</p>").arg(Toolbox.fCut(cut.maximum)))
        if cut.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>%1</code></p>").arg(cut.comment))
        self.setText(content.join(""))
        # Show charts if available.
        if cut.type == tmGrammar.ETA:
            self.setEtaCutChart(float(cut.minimum), float(cut.maximum))
        elif cut.type == tmGrammar.PHI:
            self.setPhiCutChart(float(cut.minimum), float(cut.maximum))

    def loadObject(self, obj):
        self.reset()
        content = QtCore.QStringList()
        content.append(self.tr("<h2>%1</h2>").arg(obj.name))
        content.append(self.tr("<p><strong>Type:</strong> %1</p>").arg(obj.type))
        if obj.type in CountObjectTypes:
            content.append(self.tr("<p><strong>Threshold:</strong> %1 %2</p>").arg(Toolbox.fComparison(obj.comparison_operator)).arg(Toolbox.fCounts(obj.threshold)))
        else:
            content.append(self.tr("<p><strong>Threshold:</strong> %1 %2</p>").arg(Toolbox.fComparison(obj.comparison_operator)).arg(Toolbox.fThreshold(obj.threshold)))
        content.append(self.tr("<p><strong>BX offset:</strong> %1</p>").arg(Toolbox.fBxOffset(obj.bx_offset)))
        if obj.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>%1</code></p>").arg(obj.comment))
        self.setText(content.join(""))

    def loadExternal(self, menu, external):
        self.reset()
        content = QtCore.QStringList()
        content.append(self.tr("<h2>%1</h2>").arg(external.name))
        content.append(self.tr("<p><strong>BX offset:</strong> %1</p>").arg(Toolbox.fBxOffset(external.bx_offset)))
        data = filter(lambda item: item[kName] == external.signal_name, menu.extSignals.extSignals)[0]
        content.append(self.tr("<p><strong>System:</strong> %1</p>").arg(data[kSystem]))
        if kLabel in data.keys():
            content.append(self.tr("<p><strong>Label:</strong> %1</p>").arg(data[kLabel]))
        content.append(self.tr("<p><strong>Cable:</strong> %1</p>").arg(data[kCable]))
        content.append(self.tr("<p><strong>Channel:</strong> %1</p>").arg(data[kChannel]))
        if kDescription in data.keys():
            content.append(self.tr("<p><strong>Description:</strong> %1</p>").arg(data[kDescription]))
        if external.comment:
            content.append(self.tr("<p><strong>Comment:</strong></p>"))
            content.append(self.tr("<p><code>%1</code></p>").arg(external.comment))
        self.setText(content.join(""))

    def loadScale(self, data): # TODO
        self.reset()
        content = QtCore.QStringList()
        content.append(self.tr("<p><strong>Object:</strong> %1</p>").arg(data[kObject]))
        content.append(self.tr("<p><strong>Type:</strong> %1</p>").arg(data[kType]))
        content.append(self.tr("<p><strong>Minimum:</strong> %1</p>").arg(Toolbox.fCut(data[kMinimum])))
        content.append(self.tr("<p><strong>Maximum:</strong> %1</p>").arg(Toolbox.fCut(data[kMaximum])))
        content.append(self.tr("<p><strong>Step:</strong> %1</p>").arg(Toolbox.fCut(data[kStep])))
        content.append(self.tr("<p><strong>Bitwidth:</strong> %1</p>").arg(data[kNBits]))
        self.setText(content.join(""))

    def loadScaleType(self, name, data): # TODO
        self.reset()
        content = QtCore.QStringList()
        content.append(self.tr("<h2>Scale %1</h2>").arg(name))
        content.append(self.tr("<p><strong>Number:</strong> %1</p>").arg(data[kNumber]))
        content.append(self.tr("<p><strong>Minimum:</strong> %1</p>").arg(Toolbox.fCut(data[kMinimum])))
        content.append(self.tr("<p><strong>Maximum:</strong> %1</p>").arg(Toolbox.fCut(data[kMaximum])))
        self.setText(content.join(""))

    def loadSignal(self, data): # TODO
        self.reset()
        content = QtCore.QStringList()
        content.append(self.tr("<h2>%1</h2>").arg(data[kName]))
        content.append(self.tr("<p><strong>System:</strong> %1</p>").arg(data[kSystem]))
        content.append(self.tr("<p><strong>Name:</strong> %1</p>").arg(data[kName]))
        if kLabel in data.keys():
            content.append(self.tr("<p><strong>Label:</strong> %1</p>").arg(data[kLabel]))
        content.append(self.tr("<p><strong>Cable:</strong> %1</p>").arg(data[kCable]))
        content.append(self.tr("<p><strong>Channel:</strong> %1</p>").arg(data[kChannel]))
        if kDescription in data.keys():
            content.append(self.tr("<p><strong>Description:</strong> %1</p>").arg(data[kDescription]))
        self.setText(content.join(""))
