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
        self.setModified(False)
        #
        self.indexComboBox = QComboBox(self)
        self.indexComboBox.setEditable(True)
        self.indexComboBox.setMinimumWidth(50)
        self.nameComboBox = QLineEdit(self)
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
        self.textEdit.textChanged.connect(self.onTextChanged)

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
        self.libraryWidget.selected.connect(self.onInsertItem)
        dock.setWidget(self.libraryWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def index(self):
        return int(self.indexComboBox.currentText())

    def setIndex(self, index):
        self.indexComboBox.setEditText(str(index))

    def name(self):
        return self.nameComboBox.text()

    def setName(self, name):
        self.nameComboBox.setText(name)

    def expression(self):
        """Returns a machine readable formatted version of the loaded algorithm."""
        return self.formatter.machinize(str(self.textEdit.toPlainText()))

    def setExpression(self, expression):
        self.textEdit.setPlainText(self.formatter.humanize(expression))

    def comment(self):
        return ""

    def setComment(self, comment):
        pass

    def isModified(self):
        return self._isModified

    def setModified(self, modified):
        self._isModified = bool(modified)

    def onTextChanged(self):
        self.setModified(True)

    def onFormatCompact(self):
        modified = self.isModified() # Foramtting does not count as change.
        self.textEdit.setPlainText(self.formatter.humanize(self.expression()))
        self.setModified(modified)

    def onFormatExpand(self):
        modified = self.isModified() # Foramtting does not count as change.
        self.textEdit.setPlainText(self.formatter.expanded(self.expression()))
        self.setModified(modified)

    def onInsertItem(self, text):
        """Inserts text. Automatically adds spaces to separate tokens in a
        convenient and helpful maner.
        """
        cursor = self.textEdit.textCursor()
        ref = str(self.textEdit.toPlainText()) # to python string
        # Get text cursor position/selection slice.
        start, end = sorted((cursor.position(), cursor.anchor()))
        # If selection does not start at begin of document
        if start > 0:
            # Check previous character and add required whitespace
            if not ref[start - 1] in " [\t\r\n":
                text = " " + text
        # If selection does not end at end of document
        if end < (len(ref) - 1):
            # Check following character and add required whitespace
            if not ref[end] in " ,][\t\r\n":
                text = text + " "
        cursor.insertText(text)
        self.textEdit.ensureCursorVisible()

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

    def closeEvent(self, event):
        """On window close event."""
        if self.editor.isModified():
            reply = QMessageBox.warning(self, "Close algorithm editor",
                QString("The algorithm \"%1\" has been modified.\n" \
                        "Do you want to apply your changes or discard them?").arg(self.name()),
                QMessageBox.Cancel | QMessageBox.Close | QMessageBox.Apply, QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.Apply:
                event.accept()
                self.accept()
                return
        event.accept()
        self.reject()

# -----------------------------------------------------------------------------
#  Library widget
# -----------------------------------------------------------------------------

class LibraryWidget(QWidget):

    selected = pyqtSignal(str)

    Functions = (
        ("comb{obj, obj}", "Double combination function, returns true if both object requirements are fulfilled.",),
        ("comb{obj, obj, obj}", "Triple combination function, returns true if all three object requirements are fulfilled.",),
        ("comb{obj, obj, obj, obj}", "Quad combination function, returns true if all four object requirements are fulfilled.",),
        ("dist{obj, obj}[cut]", "Correlation function, retruns true if correlation of both object requirements is within the given cut.",),
        ("dist{obj, obj}[cut, cut]", "Correlation function, retruns true if correlation of both object requirements is within the given cuts.",),
        ("mass{obj, obj}[cut]", "Invariant mass function, returns true if the invariant mass of two object requirements is between the given cut.",),
    )
    Operators = (
        ("AND", "Logical AND operator.",),
        ("OR", "Logical OR operator.",),
        ("XOR", "Logical XOR operator.",),
        ("NOT", "Logical NOT operator.",),
    )
    ObjectPreview = "<br/>".join((
        "<strong>Name:</strong> {name}",
        "<strong>Type:</strong> {type}",
        "<strong>Comp. operator:</strong> {comparison_operator}",
        "<strong>Threshold:</strong> {threshold}",
        "<strong>BX offset:</strong> {bx_offset}",
    ))
    CutPreview = "<br/>".join((
        "<strong>Name:</strong> {name}",
        "<strong>Object:</strong> {object}",
        "<strong>Type:</strong> {type}",
        "<strong>Minimum:</strong> {minimum}",
        "<strong>Maximum:</strong> {maximum}",
        "<strong>Data:</strong> {data}",
    ))
    ExternalPreview = "<br/>".format((
        "<strong>Name:</strong> {name}",
        "<strong>BX offset:</strong> {bx_offset}",
        "<strong>Comment:</strong> {bx_offset}",
    ))

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
        self.functionsList.addItems([name for name, _ in self.Functions])
        self.tabWidget.addTab(self.functionsList, "&Funcs")
        # Build list of operators.
        self.operatorsList = QListWidget(self)
        self.operatorsList.addItems([name for name, _ in self.Operators])
        self.tabWidget.addTab(self.operatorsList, "O&ps")
        # Insert button.
        self.insertButton = QPushButton(self.tr("<< &Insert"), self)
        self.insertButton.clicked.connect(self.onInsert)
        self.insertButton.setDefault(False)
        # Wizard option.
        self.wizardCheckBox = QCheckBox(self.tr("Use &wizard"), self)
        # Preview widget.
        self.previewLabel = QTextEdit(self)
        self.previewLabel.setReadOnly(True)
        # Create list contents.
        self.initContents()
        # Layout
        gridLayout = QGridLayout()
        gridLayout.setContentsMargins(1, 1, 1, 1)
        gridLayout.addWidget(self.tabWidget, 0, 0, 1, 2)
        gridLayout.addWidget(self.insertButton, 1, 0)
        gridLayout.addWidget(self.wizardCheckBox, 1, 1)
        gridLayout.addWidget(self.previewLabel, 2, 0, 1, 2)
        self.setLayout(gridLayout)
        # Setup connections.
        self.objectsList.currentRowChanged.connect(self.onPreview)
        self.objectsList.itemDoubleClicked.connect(self.onInsert)
        self.cutsList.currentRowChanged.connect(self.onPreview)
        self.cutsList.itemDoubleClicked.connect(self.onInsert)
        self.externalsList.currentRowChanged.connect(self.onPreview)
        self.externalsList.itemDoubleClicked.connect(self.onInsert)
        self.functionsList.currentRowChanged.connect(self.onPreview)
        self.functionsList.itemDoubleClicked.connect(self.onInsert)
        self.operatorsList.currentRowChanged.connect(self.onPreview)
        self.operatorsList.itemDoubleClicked.connect(self.onInsert)
        self.tabWidget.currentChanged.connect(self.onPreview)

    def initContents(self):
        """Populate library lists with content from menu."""
        # Build list of objects.
        self.objectsList.clear()
        self.objectsList.addItems(sorted([obj.name for obj in self.menu.objects]))
        # Build list of cuts.
        self.cutsList.clear()
        self.cutsList.addItems(sorted([cut.name for cut in self.menu.cuts]))
        # Build list of externals.
        self.externalsList.clear()
        self.externalsList.addItems(sorted([external.name for external in self.menu.externals]))
        # Refresh UI.
        self.onPreview()

    def onPreview(self):
        """Updates preview widget with current selected library item."""
        self.previewLabel.setText("")
        self.insertButton.setEnabled(False)
        self.wizardCheckBox.setEnabled(False)
        tab = self.tabWidget.currentWidget()
        # Objects
        if tab == self.objectsList:
            if not self.objectsList.currentItem(): return # empty list
            item = self.menu.objectByName(self.objectsList.currentItem().text())
            self.wizardCheckBox.setEnabled(True)
            if not item: return
            item = dict(**item) # Copy
            item['threshold'] = Toolbox.fThreshold(item['threshold'])
            item['bx_offset'] = Toolbox.fBxOffset(item['bx_offset'])
            self.previewLabel.setText(self.ObjectPreview.format(**item))
            self.insertButton.setEnabled(True)
        # Cuts
        elif tab == self.cutsList:
            if not self.cutsList.currentItem(): return # empty list
            item = self.menu.cutByName(self.cutsList.currentItem().text())
            if not item: return
            item = dict(**item) # Copy
            item['minimum'] = Toolbox.fCut(item['minimum'])
            item['maximum'] = Toolbox.fCut(item['maximum'])
            item['data'] = item['data'] or '-'
            self.previewLabel.setText(self.CutPreview.format(**item))
            self.insertButton.setEnabled(True)
        # Externals
        elif tab == self.externalsList:
            if not self.externalsList.currentItem(): return # empty list
            item = self.menu.externalByName(self.externalsList.currentItem().text())
            if not item: return
            self.previewLabel.setText(self.ExternalPreview.format(**item))
            self.insertButton.setEnabled(True)
        # Functions
        elif tab == self.functionsList:
            row = self.functionsList.currentRow()
            self.wizardCheckBox.setEnabled(True)
            if row < 0: return
            self.previewLabel.setText(self.Functions[row][1])
            self.insertButton.setEnabled(True)
        # Operators
        elif tab == self.operatorsList:
            row = self.operatorsList.currentRow()
            if row < 0: return
            self.previewLabel.setText(self.Operators[row][1])
            self.insertButton.setEnabled(True)

    def onInsert(self):
        """Insert selected item from active library list."""
        self.selected.emit(self.tabWidget.currentWidget().currentItem().text())