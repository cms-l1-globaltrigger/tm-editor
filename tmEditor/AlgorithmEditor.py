# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm editor main window and dialog.
"""

from tmEditor import AlgorithmFormatter
from tmEditor import AlgorithmSyntaxHighlighter
from tmEditor import Toolbox
from tmEditor import Menu
from tmEditor.Menu import Algorithm

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import sys, os

class AlgorithmEditor(QMainWindow):

    def __init__(self, menu, parent = None):
        super(AlgorithmEditor, self).__init__(parent)
        # Setup window
        self.setWindowTitle(self.tr("Algorithm Editor"))
        self.resize(720, 480)
        self.menu = menu
        self.formatter = AlgorithmFormatter()
        # Create actions and toolbars.
        self.createActions()
        self.createMenus()
        self.createToolbar()
        # Setup main widgets
        self.textEdit = QTextEdit(self)
        font = self.textEdit.font()
        font.setFamily("Monospace")
        self.textEdit.setFont(font)
        self.textEdit.setFrameShape(QFrame.NoFrame)
        self.textEdit.setCursorWidth(2)
        # Setup editor syntax highlighter.
        self.highlighter = AlgorithmSyntaxHighlighter(self.textEdit)
        # Setup layout
        self.setCentralWidget(self.textEdit)
        # Setup dock widgets
        dock = QDockWidget(self.tr("Settings"), self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.settingsWidget = QWidget(self)
        self.indexComboBox = QComboBox(self)
        self.indexComboBox.setEditable(True)
        layout = QVBoxLayout()
        layout.addWidget(self.indexComboBox)
        self.settingsWidget.setLayout(layout)
        dock.setWidget(self.settingsWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        #
        dock = QDockWidget(self.tr("Library"), self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.libraryWidget = LibraryWidget(self.menu, dock)
        self.libraryWidget.selected.connect(self.insertItem)
        dock.setWidget(self.libraryWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        # Setup properties (as last step).
        self.setIndex(0)
        self.setName(self.tr("L1_Unnamed"))
        self.setExpression("")
        self.setComment("")

    def insertItem(self, text):
        self.textEdit.textCursor().insertText(text)
        self.textEdit.ensureCursorVisible()

    def createActions(self):
        self.formatCompactAct = QAction(self.tr("&Compact"), self)
        self.formatCompactAct.setIcon(Toolbox.createIcon('actions', 'zoom-out'))
        self.formatCompactAct.triggered.connect(self.onFormatCompact)
        self.formatExpandAct = QAction(self.tr("&Expand"), self)
        self.formatExpandAct.setIcon(Toolbox.createIcon('actions', 'zoom-in'))
        self.formatExpandAct.triggered.connect(self.onFormatExpand)

    def createMenus(self):
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.formatMenu = self.menuBar().addMenu(self.tr("&Format"))
        self.formatMenu.addAction(self.formatCompactAct)
        self.formatMenu.addAction(self.formatExpandAct)
        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))

    def createToolbar(self):
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        # self.toolbar.addSeparator()
        self.toolbar.addAction(self.formatCompactAct)
        self.toolbar.addAction(self.formatExpandAct)

    def index(self):
        return int(self.indexComboBox.currentText())

    def setIndex(self, index):
        self.indexComboBox.setEditText(str(index))

    def name(self):
        return ""

    def setName(self, name):
        pass

    def expression(self):
        """Returns a machine readable formatted version of the loaded algorithm."""
        return self.formatter.machinize(str(self.textEdit.toPlainText()))

    def comment(self):
        return ""

    def setComment(self, comment):
        pass

    def setExpression(self, expression):
        self.textEdit.setPlainText(self.formatter.humanize(expression))

    def onFormatCompact(self):
        self.textEdit.setPlainText(self.formatter.humanize(self.expression()))

    def onFormatExpand(self):
        self.textEdit.setPlainText(self.formatter.expanded(self.expression()))

    def closeEvent(self, event):
        """On window close event."""
        #event.ignore()
        event.accept()

class AlgorithmEditorDialog(QDialog):
    """Dialog wrapper for algorithm editor main window."""

    def __init__(self, menu, parent = None):
        super(AlgorithmEditorDialog, self).__init__(parent)
        self.algorithmEditor = AlgorithmEditor(menu)
        self.setWindowTitle(self.algorithmEditor.windowTitle())
        self.resize(720, 480)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.algorithmEditor)
        bottomLayout = QVBoxLayout()
        bottomLayout.addWidget(buttonBox)
        bottomLayout.setContentsMargins(10, 0, 10, 10)
        layout.addLayout(bottomLayout)
        self.setLayout(layout)

    def index(self):
        return self.algorithmEditor.index()

    def setIndex(self, index):
        self.algorithmEditor.setIndex(index)

    def name(self):
        return self.algorithmEditor.name()

    def setName(self, name):
        self.algorithmEditor.setName(name)

    def expression(self):
        return self.algorithmEditor.expression()

    def setExpression(self, expression):
        self.algorithmEditor.setExpression(expression)

    def comment(self):
        return self.algorithmEditor.comment()

    def setComment(self, comment):
        self.algorithmEditor.setComment(comment)

class LibraryWidget(QWidget):

    selected = pyqtSignal(str)

    def __init__(self, menu, parent = None):
        super(LibraryWidget, self).__init__(parent)
        self.menu = menu
        self.tabWidget = QTabWidget(self)
        # Build list of objects.
        self.objectsList = QListWidget(self)
        self.tabWidget.addTab(self.objectsList, "&Objects")
        # Build list of cuts.
        self.cutsList = QListWidget(self)
        self.tabWidget.addTab(self.cutsList, "&Cuts")
        # Build list of externals.
        self.externalsList = QListWidget(self)
        self.tabWidget.addTab(self.externalsList, "&Exts")
        # Build list of function templates.
        self.functionsList = QListWidget(self)
        self.functionsList.addItems([
            "comb{obj, obj}",
            "comb{obj, obj, obj}",
            "comb{obj, obj, obj, obj}",
            "dist{obj, obj}[cut]",
            "dist{obj, obj}[cut, cut]",
            "mass{obj, obj}[cut]",
        ])
        self.tabWidget.addTab(self.functionsList, "&Funcs")
        # Build list of operators.
        self.operatorsList = QListWidget(self)
        self.operatorsList.addItems([
            "AND",
            "OR",
            "NOT",
        ])
        self.tabWidget.addTab(self.operatorsList, "O&ps")
        # Layout
        gridLayout = QGridLayout()
        gridLayout.setContentsMargins(1, 1, 1, 1)
        gridLayout.addWidget(self.tabWidget, 0, 0, 1, 2)
        self.previewLabel = QTextEdit("&Preview")
        self.previewLabel.setReadOnly(True)
        gridLayout.addWidget(self.previewLabel, 1, 0, 1, 2)
        # gridLayout.addWidget(QPushButton("<< &Insert"), 2, 0, 1, 1)
        # gridLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum), 2, 1, 1, 1)
        self.setLayout(gridLayout)
        self.objectsList.currentRowChanged.connect(self.setPreview)
        self.objectsList.itemDoubleClicked.connect(self.insertObject)
        self.cutsList.currentRowChanged.connect(self.setPreview)
        self.cutsList.itemDoubleClicked.connect(self.insertCut)
        self.externalsList.currentRowChanged.connect(self.setPreview)
        self.externalsList.itemDoubleClicked.connect(self.insertExternal)
        self.functionsList.itemDoubleClicked.connect(self.insertFunction)
        self.operatorsList.itemDoubleClicked.connect(self.insertOperator)
        self.tabWidget.currentChanged.connect(self.setPreview)
        self.reloadMenu()

    def setPreview(self):
        # TODO clean up, not effective
        if self.tabWidget.currentIndex() == 0: # Objects
            row = self.objectsList.currentRow()
            self.previewLabel.setText('<br/>'.join(["<strong>{0}</strong>: {1}".format(key, value) for key, value in self.menu.objects[row].items()]))
        elif self.tabWidget.currentIndex() == 1: # Cuts
            row = self.cutsList.currentRow()
            self.previewLabel.setText('<br/>'.join(["<strong>{0}</strong>: {1}".format(key, value) for key, value in self.menu.cuts[row].items()]))
        else:
            self.previewLabel.setText("")

    def insertObject(self):
        self.selected.emit(self.objectsList.currentItem().text())

    def insertCut(self):
        self.selected.emit(self.cutsList.currentItem().text())

    def insertExternal(self):
        self.selected.emit(self.externalsList.currentItem().text())

    def insertFunction(self):
        self.selected.emit(self.functionsList.currentItem().text())

    def insertOperator(self):
        self.selected.emit(Toolbox.fSeparate(self.operatorsList.currentItem().text()))

    def reloadMenu(self):
        # TODO clean up
        # Build list of objects.
        self.objectsList.clear()
        self.objectsList.addItems(sorted([obj['name'] for obj in self.menu.objects]))
        # Build list of cuts.
        self.cutsList.clear()
        self.cutsList.addItems(sorted([cut['name'] for cut in self.menu.cuts]))
