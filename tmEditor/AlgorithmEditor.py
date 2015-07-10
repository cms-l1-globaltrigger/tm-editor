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

# -----------------------------------------------------------------------------
#  Algorithm editor window
# -----------------------------------------------------------------------------

class AlgorithmEditor(QMainWindow):
    """Algorithm editor class."""

    def __init__(self, menu, parent = None):
        super(AlgorithmEditor, self).__init__(parent)
        # Setup window
        self.setWindowTitle(self.tr("Algorithm Editor"))
        self.resize(720, 480)
        self.menu = menu
        self.formatter = AlgorithmFormatter()
        #
        self.indexComboBox = QComboBox(self)
        self.indexComboBox.setEditable(True)
        self.indexComboBox.setMinimumWidth(50)
        self.nameComboBox = QComboBox(self)
        self.nameComboBox.setEditable(True)
        self.nameComboBox.setMinimumWidth(300)
        # Create actions and toolbars.
        self.createActions()
        self.createMenus()
        self.createToolbar()
        self.createDocks()
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
        # Setup properties (as last step).
        self.setIndex(0)
        self.setName(self.tr("L1_Unnamed"))
        self.setExpression("")
        self.setComment("")

    def insertItem(self, text):
        self.textEdit.textCursor().insertText(text)
        self.textEdit.ensureCursorVisible()

    def createActions(self):
        """Create actions."""
        self.formatCompactAct = QAction(self.tr("&Compact"), self)
        self.formatCompactAct.setIcon(Toolbox.createIcon('actions', 'zoom-out'))
        self.formatCompactAct.triggered.connect(self.onFormatCompact)
        self.formatExpandAct = QAction(self.tr("&Expand"), self)
        self.formatExpandAct.setIcon(Toolbox.createIcon('actions', 'zoom-in'))
        self.formatExpandAct.triggered.connect(self.onFormatExpand)

    def createMenus(self):
        """Create menus."""
        # self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.formatMenu = self.menuBar().addMenu(self.tr("&Format"))
        self.formatMenu.addAction(self.formatCompactAct)
        self.formatMenu.addAction(self.formatExpandAct)
        # self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))

    def createToolbar(self):
        """Create toolbars."""
        # Setup toolbars
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        # self.toolbar.addSeparator()
        self.toolbar.addAction(self.formatCompactAct)
        self.toolbar.addAction(self.formatExpandAct)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel(self.tr("  Name "), self))
        self.toolbar.addWidget(self.nameComboBox)
        self.toolbar.addWidget(QLabel(self.tr("  Index "), self))
        self.toolbar.addWidget(self.indexComboBox)

    def createDocks(self):
        """Create dock widgets."""
        # Setup library
        dock = QDockWidget(self.tr("Library"), self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.libraryWidget = LibraryWidget(self.menu, dock)
        self.libraryWidget.selected.connect(self.insertItem)
        dock.setWidget(self.libraryWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def index(self):
        return int(self.indexComboBox.currentText())

    def setIndex(self, index):
        self.indexComboBox.setEditText(str(index))

    def name(self):
        return self.nameComboBox.currentText()

    def setName(self, name):
        self.nameComboBox.setEditText(name)

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
        event.accept()

# -----------------------------------------------------------------------------
#  Algorithm editor dialog (modal)
# -----------------------------------------------------------------------------

class AlgorithmEditorDialog(QDialog):
    """Algorithm editor dialog class."""

    def __init__(self, menu, parent = None):
        super(AlgorithmEditorDialog, self).__init__(parent)
        self.editor = AlgorithmEditor(menu)
        self.setWindowTitle(self.editor.windowTitle())
        self.resize(720, 480)
        self.setSizeGripEnabled(True)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        bottomLayout = QVBoxLayout()
        bottomLayout.addWidget(buttonBox)
        bottomLayout.setContentsMargins(10, 0, 10, 10)
        layout.addLayout(bottomLayout)
        self.setLayout(layout)

    def index(self):
        """Provided for convenience."""
        return self.editor.index()

    def setIndex(self, index):
        """Provided for convenience."""
        self.editor.setIndex(index)

    def name(self):
        """Provided for convenience."""
        return self.editor.name()

    def setName(self, name):
        """Provided for convenience."""
        self.editor.setName(name)

    def expression(self):
        """Provided for convenience."""
        return self.editor.expression()

    def setExpression(self, expression):
        """Provided for convenience."""
        self.editor.setExpression(expression)

    def comment(self):
        """Provided for convenience."""
        return self.editor.comment()

    def setComment(self, comment):
        """Provided for convenience."""
        self.editor.setComment(comment)

# -----------------------------------------------------------------------------
#  Library widget
# -----------------------------------------------------------------------------

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
        # Create list contents.
        self.initContents()
        # Layout
        gridLayout = QGridLayout()
        gridLayout.setContentsMargins(1, 1, 1, 1)
        gridLayout.addWidget(self.tabWidget, 0, 0, 1, 2)
        self.previewLabel = QTextEdit(self)
        self.previewLabel.setReadOnly(True)
        gridLayout.addWidget(self.previewLabel, 1, 0, 1, 2)
        # gridLayout.addWidget(QPushButton("<< &Insert"), 2, 0, 1, 1)
        # gridLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum), 2, 1, 1, 1)
        self.setLayout(gridLayout)
        # Setup connections.
        self.objectsList.currentRowChanged.connect(self.showPreview)
        self.objectsList.itemDoubleClicked.connect(self.insertObject)
        self.cutsList.currentRowChanged.connect(self.showPreview)
        self.cutsList.itemDoubleClicked.connect(self.insertCut)
        self.externalsList.currentRowChanged.connect(self.showPreview)
        self.externalsList.itemDoubleClicked.connect(self.insertExternal)
        self.functionsList.currentRowChanged.connect(self.showPreview)
        self.functionsList.itemDoubleClicked.connect(self.insertFunction)
        self.operatorsList.currentRowChanged.connect(self.showPreview)
        self.operatorsList.itemDoubleClicked.connect(self.insertOperator)
        self.tabWidget.currentChanged.connect(self.showPreview)

    def initContents(self):
        # Build list of objects.
        self.objectsList.clear()
        self.objectsList.addItems(sorted([obj['name'] for obj in self.menu.objects]))
        # Build list of cuts.
        self.cutsList.clear()
        self.cutsList.addItems(sorted([cut['name'] for cut in self.menu.cuts]))
        # Build list of externals.
        self.externalsList.clear()
        self.externalsList.addItems(sorted([external['name'] for external in self.menu.externals]))

    def showPreview(self):
        """Updates preview widget with current selected library item."""
        index = self.tabWidget.currentIndex()
        if index == 0: # Objects
            row = self.objectsList.currentRow()
            if row < 0:
                self.previewLabel.setText("")
                return
            items = dict(**self.menu.objects[row])
            items['threshold'] = Toolbox.fThreshold(items['threshold'])
            items['bx_offset'] = Toolbox.fBxOffset(items['bx_offset'])
            self.previewLabel.setText("""
                <strong>Name:</strong> {name}<br/>
                <strong>Type:</strong> {type}<br/>
                <strong>Comp. operator:</strong> {comparison_operator}<br/>
                <strong>Threshold:</strong> {threshold}<br/>
                <strong>BX offset:</strong> {bx_offset}
            """.format(**items))
        elif index == 1: # Cuts
            row = self.cutsList.currentRow()
            if row < 0:
                self.previewLabel.setText("")
                return
            items = dict(**self.menu.cuts[row])
            items['minimum'] = Toolbox.fCut(items['minimum'])
            items['maximum'] = Toolbox.fCut(items['maximum'])
            items['data'] = items['data'] or '-'
            self.previewLabel.setText("""
                <strong>Name:</strong> {name}<br/>
                <strong>Object:</strong> {object}<br/>
                <strong>Type:</strong> {type}<br/>
                <strong>Minimum:</strong> {minimum}<br/>
                <strong>Maximum:</strong> {maximum}<br/>
                <strong>Data:</strong> {data}
            """.format(**items))
        elif index == 2: # Externals
            row = self.externalsList.currentRow()
            if row < 0:
                self.previewLabel.setText("")
                return
            self.previewLabel.setText('<br/>'.join(["<strong>{0}</strong>: {1}".format(key, value) for key, value in self.menu.externals[row].items()]))
        elif index == 3: # Functions
            row = self.functionsList.currentRow()
            self.previewLabel.setText([
                "Double combination function, returns true if both object requirements are fulfilled.",
                "Triple combination function, returns true if all three object requirements are fulfilled.",
                "Quad combination function, returns true if all four object requirements are fulfilled.",
                "Correlation function, retruns true if correlation of both object requirements is within the given cut.",
                "Correlation function, retruns true if correlation of both object requirements is within the given cuts.",
                "Invariant mass function, returns true if the invariant mass of two object requirements is between the given cut.",
            ][row])
        elif index == 4: # Operators
            row = self.operatorsList.currentRow()
            self.previewLabel.setText([
                "Logical AND operator.",
                "Logical OR operator.",
                "Logical NOT operator.",
            ][row])
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
