"""Algorithm editor main window and dialog.

class ExpressionCodeEditor
class AlgorithmEditor
class AlgorithmEditorDialog
class MessageBarWidget
"""

import logging
import re
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import tmGrammar

from tmEditor.core.Algorithm import Algorithm, External
from tmEditor.core.Settings import MaxAlgorithms
from tmEditor.core.Algorithm import RegExObject, RegExSignal, RegExExtSignal, RegExFunction
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError
from tmEditor.core.XmlDecoder import mirgrate_mass_function # HACK
from tmEditor.core.toolbox import encode_labels, decode_labels

from tmEditor.gui.AlgorithmSyntaxHighlighter import AlgorithmSyntaxHighlighter
from tmEditor.gui.CodeEditor import CodeEditor

from tmEditor.gui.ObjectEditorDialog import ObjectEditorDialog
from tmEditor.gui.ExtSignalEditorDialog import ExtSignalEditorDialog
from tmEditor.gui.FunctionEditorDialog import FunctionEditorDialog
from tmEditor.gui.AlgorithmSelectIndexDialog import AlgorithmSelectIndexDialog

# Common widgets
from tmEditor.gui.CommonWidgets import RestrictedLineEdit
from tmEditor.gui.CommonWidgets import ListSpinBox
from tmEditor.gui.CommonWidgets import richTextObjectsPreview
from tmEditor.gui.CommonWidgets import richTextSignalsPreview
from tmEditor.gui.CommonWidgets import richTextExtSignalsPreview
from tmEditor.gui.CommonWidgets import richTextCutsPreview
from tmEditor.gui.CommonWidgets import createIcon

__all__ = ['AlgorithmEditorDialog', ]

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kName = 'name'

ContentsURL = "https://cern.ch/globaltrigger/upgrade/tme/userguide#create-algorithms"

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def findObject(text, pos):
    """Returns object requirement at position *pos* or None if nothing found."""
    for result in RegExObject.finditer(text):
        if result.start() <= pos < result.end():
            if not result.group(0).startswith(tmGrammar.EXT): # Exclude EXT signals
                return result.group(0), result.start(), result.end()
    for result in RegExSignal.finditer(text):
        if result.start() <= pos < result.end():
            if not result.group(0).startswith(tmGrammar.EXT): # Exclude EXT signals
                return result.group(0), result.start(), result.end()
    return None

def findExtSignal(text, pos):
    """Returns external signal at position *pos* or None if nothing found."""
    for result in RegExExtSignal.finditer(text):
        if result.start() <= pos < result.end():
            return result.group(0), result.start(), result.end()
    return None

def findFunction(text, pos):
    """Returns function expression at position *pos* or None if nothing found."""
    for result in RegExFunction.finditer(text):
        if result.start() <= pos < result.end():
            return result.group(0), result.start(), result.end()
    return None

def currentData(widget):
    rows = widget.selectionModel().selectedRows()
    if rows:
        return rows[0].data()
    return None

# -----------------------------------------------------------------------------
#  Expression code editor
# -----------------------------------------------------------------------------

class ExpressionCodeEditor(CodeEditor):
    """Algorithm expression code editor widget with custom context menu."""

    editObject = QtCore.pyqtSignal(tuple)
    """Signal raised on edit object token request (custom context menu)."""

    editExtSignal = QtCore.pyqtSignal(tuple)
    """Signal raised on edit external signal token request (custom context menu)."""

    editFunction = QtCore.pyqtSignal(tuple)
    """Signal raised on edit function expression request (custom context menu)."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        """Custom ciontext menu providing actions to edit object and function
        expressions.
        """
        # Get context menu
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        # Add object requirement action
        objAct = menu.addAction(self.tr("Edit &Object..."))
        objAct.setEnabled(False)
        # Add external signal action
        extAct = menu.addAction(self.tr("Edit External &Signal..."))
        extAct.setEnabled(False)
        # Add function action
        funcAct = menu.addAction(self.tr("Edit &Function..."))
        funcAct.setEnabled(False)
        # Get text cursor position and expression text
        pos = self.cursorForPosition(event.pos()).position()
        text = self.toPlainText()
        # If text below pointer position
        if pos < len(text):
            # Try to locate requirement and/or function at pointer position
            objToken = findObject(text, pos)
            extToken = findExtSignal(text, pos)
            funcToken = findFunction(text, pos)
            # Enable requirement menu on success
            if objToken:
                objAct.setEnabled(True)
                objAct.triggered.connect(lambda: self.editObject.emit(objToken))
            # Enable external signal menu on success
            if extToken:
                extAct.setEnabled(True)
                extAct.triggered.connect(lambda: self.editExtSignal.emit(extToken))
            # Enable function menu on success
            if funcToken:
                funcAct.setEnabled(True)
                funcAct.triggered.connect(lambda: self.editFunction.emit(funcToken))
        # Show context menu
        menu.exec_(event.globalPos())

# -----------------------------------------------------------------------------
#  Algorithm editor window
# -----------------------------------------------------------------------------

class AlgorithmEditor(QtWidgets.QMainWindow):
    """Algorithm editor class."""

    def __init__(self, menu, parent=None):
        super().__init__(parent)
        # Setup window
        self.setWindowTitle(self.tr("Algorithm Editor"))
        self.resize(800, 500)
        self.menu = menu
        self.setModified(False)
        #
        self.indexSpinBox = ListSpinBox([0], self)
        self.updateFreeIndices()
        self.indexSpinBox.setMaximum(MaxAlgorithms)
        self.indexSpinBox.setMinimumWidth(60)
        self.nameLineEdit = RestrictedLineEdit(self)
        self.nameLineEdit.setPrefix('L1_')
        self.nameLineEdit.setRegexPattern('L1_[a-zA-Z0-9_]+')
        self.nameLineEdit.setMinimumWidth(310)
        self.previewTextBrowser = QtWidgets.QTextBrowser(self)
        self.previewTextBrowser.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.validator = AlgorithmSyntaxValidator(self.menu)
        self.loadedIndex = None
        self.objToken = None
        self.extToken = None
        self.funcToken = None
        # Create actions and toolbars.
        self.createActions()
        self.createMenus()
        self.createToolbar()
        self.createDocks()
        # Setup main widgets
        self.textEdit = ExpressionCodeEditor(self)
        self.textEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.textEdit.editObject.connect(self.onEditObject)
        self.textEdit.editExtSignal.connect(self.onEditExtSignal)
        self.textEdit.editFunction.connect(self.onEditFunction)
        self.textEdit.cursorPositionChanged.connect(self.onCursorPositionChanged)
        self.messageBar = MessageBarWidget(self)
        centralWidget = QtWidgets.QWidget(self)
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.textEdit, 0, 0)
        layout.addWidget(self.messageBar, 1, 0)
        centralWidget.setLayout(layout)
        # Setup editor syntax highlighter.
        self.highlighter = AlgorithmSyntaxHighlighter(self.textEdit.document())
        # Setup layout
        self.setCentralWidget(centralWidget)
        # Setup properties (as last step).
        self.setIndex(0)
        self.setName(self.tr("L1_Unnamed"))
        self.setExpression("")
        self.setComment("")
        self.setLabels([])
        self.textEdit.textChanged.connect(self.onTextChanged)
        self.indexSpinBox.valueChanged.connect(self.onIndexChanged)
        # Call slots
        self.parseTimer = QtCore.QTimer(self)
        self.parseTimer.setSingleShot(True)
        self.parseTimer.timeout.connect(self.onTextChangedDelayed)
        self.onTextChanged()
        self.messageBar.showMore.connect(self.onParse)
        # Store last used formatting
        self.currentFormatter = AlgorithmFormatter.normalize

    def createActions(self):
        """Create actions."""
        self.parseAct = QtWidgets.QAction(self.tr("&Check expression"), self)
        self.parseAct.setIcon(createIcon("view-refresh"))
        self.parseAct.triggered.connect(self.onParse)
        self.undoAct = QtWidgets.QAction(self.tr("&Undo"), self)
        self.undoAct.setShortcut(QtGui.QKeySequence.Undo)
        self.undoAct.setIcon(createIcon("edit-undo"))
        self.undoAct.triggered.connect(self.onUndo)
        self.redoAct = QtWidgets.QAction(self.tr("&Redo"), self)
        self.redoAct.setShortcut(QtGui.QKeySequence.Redo)
        self.redoAct.setIcon(createIcon("edit-redo"))
        self.redoAct.triggered.connect(self.onRedo)
        self.selectIndexAct = QtWidgets.QAction(self.tr("Select &Index"), self)
        self.selectIndexAct.setIcon(createIcon("select-index"))
        self.selectIndexAct.triggered.connect(self.onSelectIndex)
        self.insertObjectAct = QtWidgets.QAction(self.tr("&Object..."), self)
        self.insertObjectAct.setToolTip(self.tr("Insert Object..."))
        self.insertObjectAct.setIcon(createIcon("wizard-object"))
        self.insertObjectAct.triggered.connect(self.onInsertObject)
        self.insertExtSignalAct = QtWidgets.QAction(self.tr("External &Signal..."), self)
        self.insertExtSignalAct.setToolTip(self.tr("Insert External Signal..."))
        self.insertExtSignalAct.setIcon(createIcon("wizard-ext-signal"))
        self.insertExtSignalAct.triggered.connect(self.onInsertExtSignal)
        self.insertFunctionAct = QtWidgets.QAction(self.tr("&Function..."), self)
        self.insertFunctionAct.setToolTip(self.tr("Insert Function..."))
        self.insertFunctionAct.setIcon(createIcon("wizard-function"))
        self.insertFunctionAct.triggered.connect(self.onInsertFunction)
        self.editObjectAct = QtWidgets.QAction(self.tr("Edit &Object..."), self)
        self.editObjectAct.setIcon(createIcon("wizard-edit-object"))
        self.editObjectAct.setEnabled(False)
        self.editExtSignalAct = QtWidgets.QAction(self.tr("Edit External &Signal..."), self)
        self.editExtSignalAct.setIcon(createIcon("wizard-edit-ext-signal"))
        self.editExtSignalAct.setEnabled(False)
        self.editFunctionAct = QtWidgets.QAction(self.tr("Edit &Function..."), self)
        self.editFunctionAct.setIcon(createIcon("wizard-edit-function"))
        self.editFunctionAct.setEnabled(False)
        self.editObjectAct.triggered.connect(lambda: self.textEdit.editObject.emit(self.objToken))
        self.editExtSignalAct.triggered.connect(lambda: self.textEdit.editExtSignal.emit(self.extToken))
        self.editFunctionAct.triggered.connect(lambda: self.textEdit.editFunction.emit(self.funcToken))
        self.formatCollapseAct = QtWidgets.QAction(self.tr("&Collapse"), self)
        self.formatCollapseAct.setIcon(createIcon("format-compact"))
        self.formatCollapseAct.triggered.connect(self.onFormatCollapse)
        self.formatExpandAct = QtWidgets.QAction(self.tr("&Expand"), self)
        self.formatExpandAct.setIcon(createIcon("format-cascade"))
        self.formatExpandAct.triggered.connect(self.onFormatExpand)

    def createMenus(self):
        """Create menus."""
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.editMenu.addAction(self.parseAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.editObjectAct)
        self.editMenu.addAction(self.editExtSignalAct)
        self.editMenu.addAction(self.editFunctionAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.selectIndexAct)
        self.insertMenu = self.menuBar().addMenu(self.tr("&Insert"))
        self.insertMenu.addAction(self.insertObjectAct)
        self.insertMenu.addAction(self.insertExtSignalAct)
        self.insertMenu.addAction(self.insertFunctionAct)
        self.formatMenu = self.menuBar().addMenu(self.tr("&Format"))
        self.formatMenu.addAction(self.formatCollapseAct)
        self.formatMenu.addAction(self.formatExpandAct)
        # self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))

    def createToolbar(self):
        """Create toolbars."""
        # Setup toolbars
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.addAction(self.parseAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undoAct)
        self.toolbar.addAction(self.redoAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.editObjectAct)
        self.toolbar.addAction(self.editExtSignalAct)
        self.toolbar.addAction(self.editFunctionAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.insertObjectAct)
        self.toolbar.addAction(self.insertExtSignalAct)
        self.toolbar.addAction(self.insertFunctionAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.formatCollapseAct)
        self.toolbar.addAction(self.formatExpandAct)

    def createDocks(self):
        """Create dock widgets."""
        # Name
        dock = QtWidgets.QDockWidget(self.tr("Name"), self)
        dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        dock.setWidget(self.nameLineEdit)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        # Index
        dock = QtWidgets.QDockWidget(self.tr("Index"), self)
        dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        widget = QtWidgets.QWidget(self)
        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.indexSpinBox)
        pushButton = QtWidgets.QToolButton(self)
        pushButton.setDefaultAction(self.selectIndexAct)
        hbox.addWidget(pushButton)
        widget.setLayout(hbox)
        dock.setWidget(widget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        # Item preview text browser
        dock = QtWidgets.QDockWidget(self.tr("Used Items"), self)
        dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        dock.setWidget(self.previewTextBrowser)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        # Comment text edit
        dock = QtWidgets.QDockWidget(self.tr("Comment"), self)
        dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.commentEdit = QtWidgets.QPlainTextEdit(self)
        dock.setWidget(self.commentEdit)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        # Labels text edit
        dock = QtWidgets.QDockWidget(self.tr("Labels"), self)
        dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.labelsEdit = QtWidgets.QLineEdit(self)
        dock.setWidget(self.labelsEdit)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

    def index(self):
        return int(self.indexSpinBox.value())

    def setIndex(self, index):
        self.indexSpinBox.setValue(int(index))

    def name(self):
        return self.nameLineEdit.text()

    def setName(self, name):
        self.nameLineEdit.setText(name)

    def expression(self):
        """Returns a machine readable formatted version of the loaded algorithm."""
        expression = self.textEdit.toPlainText()
        return AlgorithmFormatter.compress(expression)

    def setExpression(self, expression):
        self.textEdit.setPlainText(AlgorithmFormatter.normalize(expression))

    def comment(self):
        return self.commentEdit.toPlainText()

    def setComment(self, comment):
        self.commentEdit.setPlainText(comment)

    def labels(self):
        return decode_labels(self.labelsEdit.text())

    def setLabels(self, labels):
        self.labelsEdit.setText(encode_labels(labels, pretty=True))

    def isModified(self):
        return self._isModified

    def setModified(self, modified):
        self._isModified = bool(modified)

    def replacePlainText(self, expression):
        cursor = self.textEdit.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QtGui.QTextCursor.Start)
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
        cursor.insertText(expression)

    def onCursorPositionChanged(self):
        """Toggle edit actions according to expression at cursor possition."""
        # Get text cursor position and expression text
        pos = self.textEdit.textCursor().position()
        if self.textEdit.textCursor().hasSelection():
            pos = pos - 1
        text = self.textEdit.toPlainText()
        self.editObjectAct.setEnabled(False)
        self.editExtSignalAct.setEnabled(False)
        self.editFunctionAct.setEnabled(False)
        # If text below pointer position
        if pos < len(text):
            # Try to locate requirement and/or function at pointer position
            self.objToken = findObject(text, pos)
            self.extToken = findExtSignal(text, pos)
            self.funcToken = findFunction(text, pos)
            # Enable requirement menu on success
            if self.objToken:
                self.editObjectAct.setEnabled(True)
            # Enable external signal menu on success
            if self.extToken:
                self.editExtSignalAct.setEnabled(True)
            # Enable function menu on success
            if self.funcToken:
                self.editFunctionAct.setEnabled(True)

    def onEditObject(self, token):
        text = self.textEdit.toPlainText()
        dialog = ObjectEditorDialog(self.menu, self)
        try:
            dialog.loadObject(token[0])
        except ValueError:
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"), token[0])
            return
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.replacePlainText(
                self.currentFormatter(
                    ''.join([
                        text[:token[1]],
                        dialog.expression(),
                        text[token[2]:],
                    ])
                )
            )

    def onEditExtSignal(self, token):
        text = self.textEdit.toPlainText()
        dialog = ExtSignalEditorDialog(self.menu, self)
        try:
            dialog.loadExtSignal(token[0])
        except ValueError:
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"), token[0])
            return
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.replacePlainText(
                self.currentFormatter(
                    ''.join([
                        text[:token[1]],
                        dialog.expression(),
                        text[token[2]:],
                    ])
                )
            )

    def onEditFunction(self, token):
        text = self.textEdit.toPlainText()
        dialog = FunctionEditorDialog(self.menu, self)
        try:
            dialog.loadFunction(AlgorithmFormatter.compress(token[0]))
        except ValueError:
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"), token[0])
            return
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.replacePlainText(
                self.currentFormatter(
                    ''.join([
                        text[:token[1]],
                        dialog.expression(),
                        text[token[2]:],
                    ])
                )
            )

    def onUndo(self):
        self.textEdit.document().undo()

    def onRedo(self):
        self.textEdit.document().redo()

    def onTextChanged(self):
        self.setModified(True)
        self.undoAct.setEnabled(self.textEdit.document().isUndoAvailable())
        self.redoAct.setEnabled(self.textEdit.document().isRedoAvailable())
        self.parseTimer.start(1000)
        self.previewTextBrowser.setText(self.tr("calculating..."))
        self.messageBar.setMessage(self.tr("parsing..."))

    def onTextChangedDelayed(self):
        self.previewTextBrowser.clear()

        # Validate expression
        try:
            self.validator.validate(self.expression())
        except AlgorithmSyntaxError as exc:
            self.messageBar.setErrorMessage(format(exc))
        else:
            self.messageBar.setMessage(self.tr("Expression OK"))

        # Render preview of alogithms components
        content = []
        algorithm = Algorithm(self.index(), self.name(), self.expression())
        try:
            content.append(richTextObjectsPreview(algorithm, self))
            content.append(richTextSignalsPreview(algorithm, self))
            content.append(richTextExtSignalsPreview(algorithm, self))
            content.append(richTextCutsPreview(self.menu, algorithm, self))
        except ValueError:
            pass
        self.previewTextBrowser.setText("".join(content))

    def onIndexChanged(self):
        pass

    def onSelectIndex(self):
        index = self.index()
        # Get list of already used indices but remove current index as it is matter of this operation.
        reserved = [i for i in range(MaxAlgorithms) if self.menu.algorithmByIndex(i) is not None]
        if index in reserved:
            reserved.remove(index)
        if self.loadedIndex in reserved:
            reserved.remove(self.loadedIndex)
        dialog = AlgorithmSelectIndexDialog(self)
        dialog.setup(reserved, [index])
        dialog.setModal(True)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            logging.debug("Selected new algorithm index %d", dialog.index)
            self.setIndex(dialog.index)

    def onInsertObject(self):
        dialog = ObjectEditorDialog(self.menu, self)
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.onInsertItem(dialog.expression())

    def onInsertExtSignal(self):
        dialog = ExtSignalEditorDialog(self.menu, self)
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.onInsertItem(dialog.expression())

    def onInsertFunction(self):
        dialog = FunctionEditorDialog(self.menu, self)
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.onInsertItem(dialog.expression())

    def onFormatCollapse(self):
        modified = self.isModified() # Formatting does not count as change.
        self.currentFormatter = AlgorithmFormatter.normalize
        self.replacePlainText(self.currentFormatter(self.expression()))
        self.setModified(modified)

    def onFormatExpand(self):
        modified = self.isModified() # Formatting does not count as change.
        self.currentFormatter = AlgorithmFormatter.expand
        self.replacePlainText(self.currentFormatter(self.expression()))
        self.setModified(modified)

    def onInsertItem(self, text):
        """Inserts text. Automatically adds spaces to separate tokens in a
        convenient and helpful maner.
        """
        cursor = self.textEdit.textCursor()
        ref = self.textEdit.toPlainText()
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

    def onParse(self):
        try:
            self.validator.validate(self.expression())
        except AlgorithmSyntaxError as exc:
            if exc.token:
                QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"), self.tr("{} near {}").format(exc, exc.token))
            else:
                QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"), format(exc))

    def updateFreeIndices(self, ignore=None):
        # Get list of free indices.
        #
        # Buggy.....
        #
        reserved = set([i for i in range(MaxAlgorithms) if self.menu.algorithmByIndex(i) is not None])
        indices = set(range(MaxAlgorithms)) - reserved
        if ignore is not None:
            indices.add(ignore)
        if indices:
            self.indexSpinBox.setValues(list(indices))
        if ignore is not None:
            self.indexSpinBox.setValue(ignore)

# -----------------------------------------------------------------------------
#  Algorithm editor dialog (modal)
# -----------------------------------------------------------------------------

class AlgorithmEditorDialog(QtWidgets.QDialog):
    """Algorithm editor dialog class."""

    def __init__(self, menu, parent=None):
        super().__init__(parent)
        self.editor = AlgorithmEditor(menu)
        self.loadedAlgorithm = None
        self.setWindowTitle(self.editor.windowTitle())
        self.resize(800, 500)
        self.setSizeGripEnabled(True)
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Help | QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.helpRequested.connect(self.showHelp)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        bottomLayout = QtWidgets.QVBoxLayout()
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

    def labels(self):
        """Provided for convenience."""
        return self.editor.labels()

    def setLabels(self, comment):
        """Provided for convenience."""
        self.editor.setLabels(comment)

    def loadAlgorithm(self, algorithm):
        self.loadedAlgorithm = algorithm
        self.setIndex(algorithm.index)
        self.setName(algorithm.name)
        self.setExpression(algorithm.expression)
        self.setComment(algorithm.comment)
        self.setLabels(algorithm.labels)
        self.editor.updateFreeIndices(int(algorithm.index)) # brrr
        self.editor.loadedIndex = int(algorithm.index)

    def updateAlgorithm(self, algorithm):
        algorithm.index = int(self.index())
        algorithm.name = self.name()
        algorithm.expression = self.expression()
        algorithm.comment = self.comment()
        algorithm.labels = self.labels()
        # Patch algorithm expression HACK
        mirgrate_mass_function(algorithm)

    def parse(self):
        try:
            # Validate algorithm expression.
            validator = AlgorithmSyntaxValidator(self.editor.menu)
            validator.validate(self.expression()) # mechanized expression
            for algorithm in self.editor.menu.algorithms:
                if algorithm is self.loadedAlgorithm:
                    continue
                if int(algorithm.index) == int(self.index()):
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.tr("Index used"),
                        self.tr("Algorithm index {} already used. Please select a different index.").format(algorithm.index)
                    )
                    return False
                if algorithm.name == self.name():
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.tr("Name used"),
                        self.tr("Algorithm name {} already used (by index {})").format(algorithm.name, algorithm.index)
                    )
                    return False
                # Check existance of cuts and external signals.
                #
            # TODO
            # Temporary limited conistency check.
            algorithm = Algorithm(self.index(), self.name(), self.expression(), self.comment(), self.labels())
            algorithm.objects()
            for name in algorithm.objects():
                pass
            algorithm.cuts()
            for name in algorithm.cuts():
                if not list(filter(lambda item: item.name == name, self.editor.menu.cuts)):
                    raise AlgorithmSyntaxError(f"Undefined cut `{name}`.", name)
            for name in algorithm.externals():
                def signal_name(name): return External(name, 0).signal_name
                if not list(filter(lambda item: item[kName] == signal_name(name), self.editor.menu.extSignals.extSignals)):
                    name = signal_name(name)
                    signalSet = self.editor.menu.extSignals.extSignalSet[kName]
                    raise AlgorithmSyntaxError(f"Undefined external signal `{name}` in current signal set `{signalSet}`.", name)
        except AlgorithmSyntaxError as exc:
            if exc.token:
                # Make sure to highlight the errornous part in the text editor.
                self.editor.setExpression(self.editor.expression()) # normalize expression
                self.editor.textEdit.moveCursor(QtGui.QTextCursor.Start)
                self.editor.textEdit.find(AlgorithmFormatter.normalize(exc.token))
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"), format(exc))
            return False
        except ValueError as exc:
            # TODO the tmGrammar parser errors are not user friendly.
            #       think about how to translate the messages in a user readable way.
            token = format(exc).strip()
            c = re.compile(r"\w+\:\:\w+\s*\'([^\']*)\'")
            result = c.match(token)
            if result:
                token = result.group(1)
            else:
                token = AlgorithmFormatter.normalize(token)
            # Make sure to highlight the errornous part in the text editor.
            self.editor.setExpression(self.editor.expression()) # normalize expression
            self.editor.textEdit.moveCursor(QtGui.QTextCursor.Start)
            self.editor.textEdit.find(token)
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid expression"), self.tr("Found invalid expression near:<br/>{}").format(token))
            return False
        return True

    def accept(self):
        if self.parse():
            super().accept()

    def reject(self):
        self.close() # Will call closeEvent

    def showHelp(self):
        """Raise remote contents help."""
        webbrowser.open_new_tab(ContentsURL)

    def closeEvent(self, event):
        """On window close event."""
        if self.editor.isModified():
            mbox = QtWidgets.QMessageBox(self)
            mbox.setIcon(QtWidgets.QMessageBox.Question)
            mbox.setWindowTitle(self.tr("Close algorithm editor"))
            mbox.setText(self.tr(
                "The algorithm \"{}\" has been modified.\n" \
                "Do you want to apply your changes or discard them?").format(self.name()))
            mbox.addButton(QtWidgets.QMessageBox.Cancel)
            mbox.addButton(QtWidgets.QMessageBox.Apply)
            mbox.addButton(QtWidgets.QPushButton(self.tr("Discard changes")), QtWidgets.QMessageBox.DestructiveRole)
            mbox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            mbox.exec_()
            if mbox.result() == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
            if mbox.result() == QtWidgets.QMessageBox.Apply:
                self.accept()
                if self.result() != QtWidgets.QDialog.Accepted:
                    event.ignore()
                    return
                event.accept()
                return
        event.accept()
        self.reject()

# -----------------------------------------------------------------------------
#  Message bar widget
# -----------------------------------------------------------------------------

class MessageBarWidget(QtWidgets.QWidget):
    """Message bar widget to show expression problems."""

    showMore = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(31)
        self.icon = QtWidgets.QLabel(self)
        self.icon.setPixmap(createIcon("dialog-warning").pixmap(16, 16))
        self.icon.setFixedSize(16, 16)
        self.message = QtWidgets.QLabel(self)
        self.message.linkActivated.connect(self.onLinkActivated)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(10, 10, 0, 0)
        layout.addWidget(self.icon)
        layout.addWidget(self.message)
        self.setLayout(layout)

    def onLinkActivated(self, link):
        if link == "#more":
            self.showMore.emit()

    def setMessage(self, text):
        self.icon.hide()
        self.message.setText("<span style=\"color:green;\">{0}</span>".format(text))
        self.message.setToolTip(text)

    def setErrorMessage(self, text, maxlength=32):
        """Set error message. If text message exceeds maxlength limit, a link
        is provided instead. Use signal showMore on to handle on click events.
        """
        self.icon.show()
        if len(text) > maxlength:
            self.message.setText("<span style=\"color:red;\">Syntax error, show <a href=\"#more\">more...</a></span>")
        else:
            self.message.setText("<span style=\"color:red;\">{0}</span>".format(text))
        self.message.setToolTip(text)
