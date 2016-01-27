#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from tmEditor.CommonWidgets import (
    PrefixedSpinBox,
    FilterLineEdit,
)

import sys, os

__all__ = ['ObjectEditor', ]

Objects = ['MU', 'EG', 'JET', 'TAU', 'ETM', 'HTM', 'ETT', 'ETM', ]

def headerItem(text):
    item = QStandardItem(text)
    item.setSelectable(False)
    font = item.font()
    font.setBold(True)
    item.setFont(font)
    return item

def cutItem(text, checked = False):
    item = QStandardItem(text)
    item.setCheckable(True)
    if checked:
        item.setCheckState(Qt.Checked)
    return item

Cuts = [
    headerItem('Eta cuts'),
    cutItem('MU-ETA_CEN (-1.4 ... +1.4)'),
    cutItem('MU-ETA_FWD (+3.1 ... +5.0)'),
    headerItem('Phi cuts'),
    cutItem('MU-PHI_TOP (0 ... 3.146)', True),
    cutItem('MU-PHI_BOTTOM (3.146 ... 6.291)'),
    headerItem('Quality cuts'),
    cutItem('MU-QLTY_LOW (0,1,2,3)'),
]

class ObjectEditor(QDialog):
    def __init__(self, parent = None):
        super(ObjectEditor, self).__init__(parent)
        self.ui = ObjectEditorUi(self)
        self.initCuts()
    def initCuts(self):
        model = QStandardItemModel(self)
        for item in Cuts:
            model.appendRow(item)
        proxy = QSortFilterProxyModel(self)
        proxy.setFilterKeyColumn(-1)
        proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        proxy.setSourceModel(model)
        self.ui.cutListView.setModel(proxy)
        self.ui.filterLineEdit.textChanged.connect(self.filterCuts)
    def filterCuts(self, text):
        # HACK: filter but ignore header items.
        self.ui.cutListView.model().setFilterRegExp(QString("%1|\scuts$").arg(QRegExp.escape(text)))

class ObjectEditorUi:
    def __init__(self, context):
        context.setWindowTitle(context.tr("Object Editor"))
        context.resize(640, 380)
        self.objectLabel = QLabel(context.tr("Object"), context)
        self.objectLabel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.typeComboBox = QComboBox(context)
        self.typeComboBox.addItems(Objects)
        self.typeComboBox.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.compareComboBox = QComboBox(context)
        self.compareComboBox.addItem('=>', '.ge.')
        self.compareComboBox.addItem('==', '.eq.')
        self.thresholdSpinBox = QDoubleSpinBox(context)
        self.thresholdSpinBox.setDecimals(1)
        self.thresholdSpinBox.setSingleStep(.5)
        self.thresholdSpinBox.setSuffix(context.tr(" GeV"))
        self.offsetSpinBox = PrefixedSpinBox(context)
        self.offsetSpinBox.setRange(-2, 2)
        self.offsetSpinBox.setValue(0)
        self.offsetSpinBox.setSuffix(context.tr(" BX"))
        self.cutLabel = QLabel(context.tr("Cuts"), context)
        self.cutLabel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.cutListView = QListView(context)
        self.cutListView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cutListView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.filterLabel = QLabel(context.tr("Filter"), context)
        self.filterLabel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.filterLineEdit = FilterLineEdit(context)
        self.infoTextEdit = QTextEdit(context)
        self.infoTextEdit.setText("<h3>Muon Object Requirement</h3><p>Valid threshold: 0.0 - 1023.5 GeV (0.5 GeV steps)</p>")
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.buttonBox = QDialogButtonBox(context)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Help|QDialogButtonBox.Apply|QDialogButtonBox.Cancel)
        layout = QGridLayout()
        layout.addWidget(self.objectLabel, 0, 0)
        hbox = QHBoxLayout()
        hbox.addWidget(self.typeComboBox)
        hbox.addWidget(self.compareComboBox)
        hbox.addWidget(self.thresholdSpinBox)
        hbox.addWidget(self.offsetSpinBox)
        layout.addLayout(hbox, 0, 1)
        layout.addWidget(self.cutLabel, 1, 0)
        layout.addWidget(self.cutListView, 1, 1)
        hbox = QHBoxLayout()
        hbox.addWidget(self.filterLabel)
        hbox.addWidget(self.filterLineEdit)
        layout.addLayout(hbox, 2, 1)
        layout.addWidget(self.infoTextEdit, 0, 2, 3, 1)
        layout.addWidget(self.buttonBox, 3, 0, 1, 3)
        context.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ObjectEditor()
    window.show()
    sys.exit(app.exec_())
