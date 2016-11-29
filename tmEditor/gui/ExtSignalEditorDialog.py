#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import tmGrammar

from tmEditor.core import Toolbox

from tmEditor.core.Algorithm import toExternal
from tmEditor.core.AlgorithmHelper import AlgorithmHelper, decode_threshold
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter

# Common widgets
from tmEditor.gui.CommonWidgets import PrefixedSpinBox

from PyQt4 import QtCore
from PyQt4 import QtGui

import sys, os
import re

__all__ = ['ExtSignalEditorDialog', ]

# -----------------------------------------------------------------------------
#  Keys
# -----------------------------------------------------------------------------

kEXT = 'EXT'
kName = 'name'
kSystem = 'system'
kCable = 'cable'
kChannel = 'channel'
kLabel = 'label'

# -----------------------------------------------------------------------------
#  External signal editor dialog class
# -----------------------------------------------------------------------------

class ExtSignalEditorDialog(QtGui.QDialog):
    """External signal editor dialog class."""

    def __init__(self, menu, parent=None):
        """Constructor, takes a reference to a menu and an optional parent."""
        super(ExtSignalEditorDialog, self).__init__(parent)
        self.menu = menu
        self.setupUi()
        # Connect signals
        self.signalComboBox.currentIndexChanged.connect(self.updateInfoText)
        self.offsetSpinBox.valueChanged.connect(self.updateInfoText)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # Initialize
        self.updateInfoText()

    def setupUi(self):
        self.setWindowIcon(Toolbox.createIcon("wizard-ext-signal"))
        self.setWindowTitle(self.tr("External Signal Editor"))
        self.resize(640, 280)
        self.signalLabel = QtGui.QLabel(self.tr("Signal"), self)
        self.signalLabel.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        self.signalComboBox = QtGui.QComboBox(self)
        self.signalComboBox.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        for signal in self.menu.extSignals.extSignals:
            self.signalComboBox.addItem(Toolbox.miniIcon('ext'), '_'.join((kEXT, signal[kName])))
        self.offsetSpinBox = PrefixedSpinBox(self)
        self.offsetSpinBox.setRange(-2, 2)
        self.offsetSpinBox.setValue(0)
        self.offsetSpinBox.setSuffix(self.tr(" BX"))
        self.infoTextEdit = QtGui.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        layout = QtGui.QGridLayout()
        layout.addWidget(self.signalLabel, 0, 0)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.signalComboBox)
        hbox.addWidget(self.offsetSpinBox)
        layout.addLayout(hbox, 0, 1)
        layout.addWidget(self.infoTextEdit, 0, 2, 3, 1)
        layout.addWidget(self.buttonBox, 3, 0, 1, 3)
        self.setLayout(layout)

    def name(self):
        """Returns external signal name."""
        return str(self.signalComboBox.currentText())

    def bxOffset(self):
        return self.offsetSpinBox.value()

    def expression(self):
        """Returns object expression selected by the inputs."""
        expression = AlgorithmHelper()
        expression.addExtSignal(
            name = self.name(),
            bx_offset = self.bxOffset(),
        )
        return AlgorithmFormatter.normalize(expression.serialize())

    def updateInfoText(self):
        """Update info box text."""
        name = toExternal(self.name()).signal_name
        signal = filter(lambda signal: signal[kName] == name, self.menu.extSignals.extSignals)[0]
        system = signal[kSystem]
        cable = signal[kCable]
        channel = signal[kChannel]
        label = signal[kLabel] if kLabel in signal else ""
        expression = self.expression()
        text = []
        text.append('<h3>External Signal Requirement</h3>')
        text.append('<p>System: {system}</p>')
        text.append('<p>Cable: {cable}</p>')
        text.append('<p>Channel: {channel}</p>')
        if label:
            text.append('<p>Label: {label}</p>')
        text.append('<h4>Preview</h4>')
        text.append('<p><pre>{expression}</pre></p>')
        self.infoTextEdit.setText(''.join(text).format(**locals()))

    def loadExtSignal(self, token):
        """Load dialog by values from external signal. Will raise a ValueError if string
        *token* is not a valid external signal.
        """
        signal = toExternal(token)
        self.signalComboBox.setCurrentIndex(self.signalComboBox.findText(signal.basename))
        self.offsetSpinBox.setValue(signal.bx_offset)

# -----------------------------------------------------------------------------
#  Unit test
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    pass
