# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm editor main window and dialog.

class ExpressionCodeEditor
class AlgorithmEditor
class AlgorithmEditorDialog
class MessageBarWidget
class LibraryWidget
class AlgorithmSelectionDialog
"""

import tmGrammar
from tmEditor import AlgorithmFormatter
from tmEditor import AlgorithmSyntaxHighlighter
from tmEditor import AlgorithmSyntaxValidator, AlgorithmSyntaxError
from tmEditor import Toolbox
from tmEditor import Menu
from tmEditor.Menu import Algorithm
from tmEditor.CodeEditor import CodeEditor
from tmEditor.ObjectEditor import ObjectEditorDialog
from tmEditor.FunctionEditor import FunctionEditorDialog
from tmEditor.CommonWidgets import (
    FilterLineEdit,
    RestrictedLineEdit,
)

from PyQt4 import QtCore
from PyQt4 import QtGui

import webbrowser
import sys, os
import logging
import re

MaxAlgorithms = 512

def miniIcon(name):
    """Returns mini icon to be used for items in list and tree views."""
    return QtGui.QIcon(":/icons/{name}.svg".format(name=name)).pixmap(13, 13)

RegExObject = re.compile(r'[\w\.]+\d+(?:[\+\-]\d+)?(?:\[[^\]]+\])?')
"""Precompiled regular expression for matching object requirements."""

RegExFunction = re.compile(r'\w+\s*\{[^\}]+\}(?:\[[^\]]+\])?')
"""Precompiled regular expression for matching function expressions."""

def findObject(text, pos):
    """Returns object requirement at position *pos* or None if nothing found."""
    for result in RegExObject.finditer(text):
        if result.start() <= pos < result.end():
            return result.group(0), result.start(), result.end()

def findFunction(text, pos):
    """Returns function expression at position *pos* or None if nothing found."""
    for result in RegExFunction.finditer(text):
        if result.start() <= pos < result.end():
            return result.group(0), result.start(), result.end()

class ExpressionCodeEditor(CodeEditor):
    """Algorithm expression code editor widget with custom context menu."""

    editObject = QtCore.pyqtSignal(tuple)
    """Signal raised on edit object token request (custom context menu)."""

    editFunction = QtCore.pyqtSignal(tuple)
    """Signal raised on edit function expression request (custom context menu)."""

    def __init__(self, parent=None):
        super(ExpressionCodeEditor, self).__init__(parent)

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
        # Add function action
        funcAct = menu.addAction(self.tr("Edit &Function..."))
        funcAct.setEnabled(False)
        # Get text cursor position and expression text
        pos = self.cursorForPosition(event.pos()).position()
        text = str(self.toPlainText())
        # If text below pointer position
        if pos < len(text):
            # Try to locate requirement and/or function at pointer position
            objToken = findObject(text, pos)
            funcToken = findFunction(text, pos)
            # Enable requirement menu on success
            if objToken:
                objAct.setEnabled(True)
                def call(): self.editObject.emit(objToken)
                objAct.triggered.connect(call)
            # Enable function menu on success
            if funcToken:
                funcAct.setEnabled(True)
                def call(): self.editFunction.emit(funcToken)
                funcAct.triggered.connect(call)
        # Show context menu
        menu.exec_(event.globalPos())

# -----------------------------------------------------------------------------
#  Algorithm editor window
# -----------------------------------------------------------------------------

class AlgorithmEditor(QtGui.QMainWindow):
    """Algorithm editor class."""

    def __init__(self, menu, parent = None):
        super(AlgorithmEditor, self).__init__(parent)
        # Setup window
        self.setWindowTitle(self.tr("Algorithm Editor"))
        self.resize(800, 500)
        self.menu = menu
        self.setModified(False)
        #
        self.indexSpinBox = Toolbox.ListSpinBox([0], self)
        self.updateFreeIndices()
        self.indexSpinBox.setMaximum(MaxAlgorithms)
        self.indexSpinBox.setMinimumWidth(60)
        self.nameLineEdit = RestrictedLineEdit(self)
        self.nameLineEdit.setPrefix('L1_')
        self.nameLineEdit.setRegexPattern('L1_[a-zA-Z0-9_]+')
        self.nameLineEdit.setMinimumWidth(300)
        self.validator = AlgorithmSyntaxValidator(self.menu)
        self.loadedIndex = None
        # Create actions and toolbars.
        self.createActions()
        self.createMenus()
        self.createToolbar()
        self.createDocks()
        # Setup main widgets
        self.textEdit = ExpressionCodeEditor(self)
        self.textEdit.setFrameShape(QtGui.QFrame.NoFrame)
        self.textEdit.editObject.connect(self.onEditObject)
        self.textEdit.editFunction.connect(self.onEditFunction)
        self.messageBar = MessageBarWidget(self)
        centralWidget = QtGui.QWidget(self)
        layout = QtGui.QGridLayout()
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
        self.textEdit.textChanged.connect(self.onTextChanged)
        self.indexSpinBox.valueChanged.connect(self.onIndexChanged)
        # Call slots
        self.parseTimer = QtCore.QTimer(self)
        self.parseTimer.setSingleShot(True)
        self.parseTimer.timeout.connect(self.onTextChangedDelayed)
        self.onTextChanged()

    def createActions(self):
        """Create actions."""
        self.parseAct = QtGui.QAction(self.tr("&Check expression"), self)
        self.parseAct.setIcon(Toolbox.createIcon("view-refresh"))
        self.parseAct.triggered.connect(self.onParse)
        self.undoAct = QtGui.QAction(self.tr("&Undo"), self)
        self.undoAct.setShortcut(QtGui.QKeySequence.Undo)
        self.undoAct.setIcon(Toolbox.createIcon("edit-undo"))
        self.undoAct.triggered.connect(self.onUndo)
        self.redoAct = QtGui.QAction(self.tr("&Redo"), self)
        self.redoAct.setShortcut(QtGui.QKeySequence.Redo)
        self.redoAct.setIcon(Toolbox.createIcon("edit-redo"))
        self.redoAct.triggered.connect(self.onRedo)
        self.selectIndexAct = QtGui.QAction(self.tr("Select &Index"), self)
        self.selectIndexAct.setIcon(Toolbox.createIcon("search"))
        self.selectIndexAct.triggered.connect(self.onSelectIndex)
        self.insertObjectAct = QtGui.QAction(self.tr("Insert &Object..."), self)
        self.insertObjectAct.setIcon(Toolbox.createIcon("wizard"))
        self.insertObjectAct.triggered.connect(self.onInsertObject)
        self.insertFunctionAct = QtGui.QAction(self.tr("Insert &Function..."), self)
        self.insertFunctionAct.setIcon(Toolbox.createIcon("wizard-function"))
        self.insertFunctionAct.triggered.connect(self.onInsertFunction)
        self.formatCollapseAct = QtGui.QAction(self.tr("&Collapse"), self)
        self.formatCollapseAct.setIcon(Toolbox.createIcon("format-compact"))
        self.formatCollapseAct.triggered.connect(self.onFormatCollapse)
        self.formatExpandAct = QtGui.QAction(self.tr("&Expand"), self)
        self.formatExpandAct.setIcon(Toolbox.createIcon("format-cascade"))
        self.formatExpandAct.triggered.connect(self.onFormatExpand)

    def createMenus(self):
        """Create menus."""
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.editMenu.addAction(self.parseAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.selectIndexAct)
        self.insertMenu = self.menuBar().addMenu(self.tr("&Insert"))
        self.insertMenu.addAction(self.insertObjectAct)
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
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.insertObjectAct)
        self.toolbar.addAction(self.insertFunctionAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.formatCollapseAct)
        self.toolbar.addAction(self.formatExpandAct)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QtGui.QLabel(self.tr("  Name "), self))
        self.toolbar.addWidget(self.nameLineEdit)
        self.toolbar.addWidget(QtGui.QLabel(self.tr("  Index "), self))
        self.toolbar.addWidget(self.indexSpinBox)
        self.toolbar.addAction(self.selectIndexAct)

    def createDocks(self):
        """Create dock widgets."""
        # Setup library
        dock = QtGui.QDockWidget(self.tr("Library"), self)
        dock.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        dock.setMinimumWidth(280)
        self.libraryWidget = LibraryWidget(self.menu, dock)
        self.libraryWidget.selected.connect(self.onInsertItem)
        dock.setWidget(self.libraryWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        dock = QtGui.QDockWidget(self.tr("Comment"), self)
        dock.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        # dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.commentEdit = QtGui.QPlainTextEdit(self)
        self.commentEdit.setMaximumHeight(42)
        dock.setWidget(self.commentEdit)
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
        expression = str(self.textEdit.toPlainText())
        return AlgorithmFormatter.compress(expression)

    def setExpression(self, expression):
        self.textEdit.setPlainText(AlgorithmFormatter.normalize(expression))

    def comment(self):
        return str(self.commentEdit.toPlainText())

    def setComment(self, comment):
        self.commentEdit.setPlainText(comment)

    def isModified(self):
        return self._isModified

    def setModified(self, modified):
        self._isModified = bool(modified)

    def replacePlainText(self, expression):
        cursor = self.textEdit.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QtGui.QTextCursor.Start);
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
        cursor.insertText(expression)

    def onEditObject(self, token):
        text = str(self.textEdit.toPlainText())
        dialog = ObjectEditorDialog(self.menu, self)
        dialog.loadObject(token[0])
        dialog.exec_()
        if dialog.result() == QtGui.QDialog.Accepted:
            self.textEdit.setPlainText(''.join((
                text[:token[1]],
                dialog.toExpression(),
                text[token[2]:],
            )))

    def onEditFunction(self, token):
        text = str(self.textEdit.toPlainText())
        dialog = FunctionEditorDialog(self.menu, self)
        dialog.loadFunction(token[0])
        dialog.exec_()
        if dialog.result() == QtGui.QDialog.Accepted:
            self.textEdit.setPlainText(''.join((
                text[:token[1]],
                dialog.toExpression(),
                text[token[2]:],
            )))

    def onUndo(self):
        self.textEdit.document().undo()

    def onRedo(self):
        self.textEdit.document().redo()

    def onTextChanged(self):
        self.setModified(True)
        self.undoAct.setEnabled(self.textEdit.document().isUndoAvailable())
        self.redoAct.setEnabled(self.textEdit.document().isRedoAvailable())
        self.parseTimer.start(1000)
        self.messageBar.setMessage(self.tr("parsing..."))

    def onTextChangedDelayed(self):
        try:
            self.validator.validate(self.expression())
        except AlgorithmSyntaxError, e:
            #if e.token:
            #    self.messageBar.setErrorMessage(self.tr("Error near token `%1' %2").arg(e.token).arg(str(e)))
            #else:
            self.messageBar.setErrorMessage(str(e))
        else:
            self.messageBar.setMessage(self.tr("Expression OK"))

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
        dialog = AlgorithmSelectionDialog(index, reserved, self)
        dialog.setModal(True)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            logging.debug("Selected new algorithm index %d", dialog.index)
            self.setIndex(dialog.index)

    def onInsertObject(self):
        dialog =ObjectEditorDialog(self.menu, self)
        dialog.exec_()
        if dialog.result() == QtGui.QDialog.Accepted:
            self.onInsertItem(dialog.toExpression())

    def onInsertFunction(self):
        dialog = FunctionEditorDialog(self.menu, self)
        dialog.exec_()
        if dialog.result() == QtGui.QDialog.Accepted:
            self.onInsertItem(dialog.toExpression())

    def onFormatCollapse(self):
        modified = self.isModified() # Formatting does not count as change.
        self.replacePlainText(AlgorithmFormatter.normalize(self.expression()))
        self.setModified(modified)

    def onFormatExpand(self):
        modified = self.isModified() # Formatting does not count as change.
        self.replacePlainText(AlgorithmFormatter.expand(self.expression()))
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

    def onWizard(self):
        dialog = ObjectEditorDialog(self.menu, self)
        selection = self.textEdit.textCursor().selection().toPlainText()
        if selection:
            try:
                # Will raise ValueError if selection is not a valid object
                dialog.loadObject(str(selection))
            except ValueError:
                # Ignore if some other text is selected
                pass
        dialog.exec_()
        if dialog.result() == QtGui.QDialog.Accepted:
            self.onInsertItem(dialog.toExpression())

    def onParse(self):
        try:
            self.validator.validate(self.expression())
        except AlgorithmSyntaxError, e:
            if e.token:
                QtGui.QMessageBox.warning(self, self.tr("Invalid expression"), self.tr("%1 near %2").arg(str(e)).arg(e.token))
            else:
                QtGui.QMessageBox.warning(self, self.tr("Invalid expression"), self.tr("%1").arg(str(e)))

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

class AlgorithmEditorDialog(QtGui.QDialog):
    """Algorithm editor dialog class."""

    def __init__(self, menu, parent = None):
        super(AlgorithmEditorDialog, self).__init__(parent)
        self.editor = AlgorithmEditor(menu)
        self.loadedAlgorithm = None
        self.setWindowTitle(self.editor.windowTitle())
        self.resize(800, 500)
        self.setSizeGripEnabled(True)
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Help | QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.helpRequested.connect(self.showHelp)
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        bottomLayout = QtGui.QVBoxLayout()
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
        return str(self.editor.name())

    def setName(self, name):
        """Provided for convenience."""
        self.editor.setName(name)

    def expression(self):
        """Provided for convenience."""
        return str(self.editor.expression())

    def setExpression(self, expression):
        """Provided for convenience."""
        self.editor.setExpression(expression)

    def comment(self):
        """Provided for convenience."""
        return str(self.editor.comment())

    def setComment(self, comment):
        """Provided for convenience."""
        self.editor.setComment(comment)

    def loadAlgorithm(self, algorithm):
        self.loadedAlgorithm = algorithm
        self.setIndex(algorithm.index)
        self.setName(algorithm.name)
        self.setExpression(algorithm.expression)
        self.setComment(algorithm.comment)
        self.editor.updateFreeIndices(int(algorithm.index)) # brrr
        self.editor.loadedIndex = int(algorithm.index)

    def updateAlgorithm(self, algorithm):
        algorithm['index'] = str(self.index())
        algorithm['name'] = self.name()
        algorithm['expression'] = self.expression()
        algorithm['comment'] = self.comment()

    def parse(self):
        try:
            # Validate algorithm expression.
            validator = AlgorithmSyntaxValidator(self.editor.menu)
            validator.validate(self.expression()) # mechanized expression
            for algorithm in self.editor.menu.algorithms:
                if algorithm is self.loadedAlgorithm:
                    continue
                if int(algorithm.index) == int(self.index()):
                    QtGui.QMessageBox.warning(self, "Index used", "Algorithm index {0} already used. Please select a different index.".format(algorithm.index))
                    return
                if algorithm.name == self.name():
                    QtGui.QMessageBox.warning(self, "Name used", "Algorithm name {0} already used (by index {1})".format(algorithm.name, algorithm.index))
                    return
                # Check existance of cuts and external signals.
                #
            # Temporary limited conistency check.
            algorithm = Algorithm(expression = self.expression())
            algorithm.objects()
            algorithm.cuts()
            for name in algorithm.cuts():
                if not filter(lambda item: item.name == name, self.editor.menu.cuts):
                    raise AlgorithmSyntaxError("Undefined cut `{name}`".format(**locals()), name)
            algorithm.externals()
        except AlgorithmSyntaxError, e:
            if e.token:
                # Make sure to highlight the errornous part in the text editor.
                self.editor.setExpression(self.editor.expression()) # normalize expression
                self.editor.textEdit.moveCursor(QtGui.QTextCursor.Start)
                self.editor.textEdit.find(AlgorithmFormatter.normalize(e.token))
            QtGui.QMessageBox.warning(self, self.tr("Invalid expression"), str(e))
            return False
        except ValueError, e:
            # TODO the tmGrammar parser errors are not user friendly.
            #       think about how to translate the messages in a user readable way.
            token = str(e).strip()
            c = re.compile("\w+\:\:\w+\s*\'([^\']*)\'")
            result = c.match(token)
            if result:
                token = result.group(1)
            else:
                token = AlgorithmFormatter.normalize(token)
            # Make sure to highlight the errornous part in the text editor.
            self.editor.setExpression(self.editor.expression()) # normalize expression
            self.editor.textEdit.moveCursor(QtGui.QTextCursor.Start)
            self.editor.textEdit.find(token)
            QtGui.QMessageBox.warning(self, self.tr("Invalid expression"), self.tr("Found invalid expression near:<br/>%1").arg(token))
            return False
        return True

    def accept(self):
        if self.parse():
            super(AlgorithmEditorDialog, self).accept()

    def reject(self):
        self.close() # Will call closeEvent

    def showHelp(self):
        """Raise remote contents help."""
        webbrowser.open_new_tab("http://globaltrigger.hephy.at/upgrade/tme/userguide#create-algorithms")

    def closeEvent(self, event):
        """On window close event."""
        if self.editor.isModified():
            mbox = QtGui.QMessageBox(self)
            mbox.setIcon(QtGui.QMessageBox.Question)
            mbox.setWindowTitle(self.tr("Close algorithm editor"))
            mbox.setText(self.tr(
                "The algorithm \"%1\" has been modified.\n" \
                "Do you want to apply your changes or discard them?").arg(self.name()))
            mbox.addButton(QtGui.QMessageBox.Cancel)
            mbox.addButton(QtGui.QMessageBox.Apply)
            mbox.addButton(QtGui.QPushButton(self.tr("Discard changes")), QtGui.QMessageBox.DestructiveRole)
            mbox.setDefaultButton(QtGui.QMessageBox.Cancel)
            mbox.exec_()
            if mbox.result() == QtGui.QMessageBox.Cancel:
                event.ignore()
                return
            if mbox.result() == QtGui.QMessageBox.Apply:
                self.accept()
                if self.result() != QtGui.QDialog.Accepted:
                    event.ignore()
                    return
                event.accept()
                return
        event.accept()
        self.reject()

# -----------------------------------------------------------------------------
#  Message bar widget
# -----------------------------------------------------------------------------

class MessageBarWidget(QtGui.QWidget):
    """Message bar widget to show expression problems."""

    def __init__(self, parent = None):
        super(MessageBarWidget, self).__init__(parent)
        self.setMaximumHeight(31)
        self.icon = QtGui.QLabel(self)
        self.icon.setPixmap(Toolbox.createIcon("dialog-warning").pixmap(16, 16))
        self.icon.setFixedSize(16, 16)
        self.message = QtGui.QTextEdit(self)
        self.message.setReadOnly(True)
        self.message.setMinimumHeight(31)
        self.message.setStyleSheet("QTextEdit {border: 0; background: transparent;}")
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(10, 10, 0, 0)
        layout.addWidget(self.icon)
        layout.addWidget(self.message)
        self.setLayout(layout)

    def setMessage(self, text):
        self.icon.hide()
        self.message.setText(QtCore.QString("<span style=\"color:green;\">%1</span>").arg(text))
        self.message.setToolTip(text)

    def setErrorMessage(self, text):
        self.icon.show()
        self.message.setText(QtCore.QString("<span style=\"color:red;\">%1</span>").arg(text))
        self.message.setToolTip(text)

# -----------------------------------------------------------------------------
#  Library widget
# -----------------------------------------------------------------------------

class LibraryWidget(QtGui.QWidget):

    selected = QtCore.pyqtSignal(str)

    Functions = (
        ("comb{obj, obj}", "<strong>Double combination function</strong><br/>Returns true if both object requirements are fulfilled.",),
        ("comb{obj, obj, obj}", "<strong>Triple combination function</strong><br/>Returns true if all three object requirements are fulfilled.",),
        ("comb{obj, obj, obj, obj}", "<strong>Quad combination function</strong><br/>Returns true if all four object requirements are fulfilled.",),
        ("dist{obj, obj}[cut]", "<strong>Correlation function</strong><br/>Retruns true if correlation of both object requirements is within the given cut.",),
        ("dist{obj, obj}[cut, cut]", "<strong>Correlation function</strong><br/>Retruns true if correlation of both object requirements is within the given cuts.",),
        ("mass{obj, obj}[cut]", "<strong>Invariant mass function</strong><br/>Returns true if the invariant mass of two object requirements is between the given cut.",),
    )
    Operators = (
        (tmGrammar.AND, "Logical <strong>AND</strong> operator.",),
        (tmGrammar.OR, "Logical <strong>OR</strong> operator.",),
        (tmGrammar.XOR, "Logical <strong>XOR</strong> (exclusive or) operator.",),
        (tmGrammar.NOT, "Logical <strong>NOT</strong> operator.",),
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
        # Filter
        self.filterBar = QtGui.QWidget(self)
        self.filterBar.setAutoFillBackground(True)
        self.filterBar.filterLabel = QtGui.QLabel(self.tr("Filter"), self.filterBar)
        self.filterBar.filterLineEdit = FilterLineEdit(self.filterBar)
        # self.filterBar.filterLineEdit.textChanged.connect()
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.filterBar.filterLabel)
        hbox.addWidget(self.filterBar.filterLineEdit)
        self.filterBar.setLayout(hbox)
        self.filterBar.setEnabled(False)
        self.filterBar.setVisible(False)

        # Tabs
        self.tabWidget = QtGui.QTabWidget(self)
        # Build list of objects.
        self.objectsTree = QtGui.QTreeWidget(self)
        self.objectsTree.headerItem().setHidden(True)
        self.tabWidget.addTab(self.objectsTree, self.tr("&Objects"))
        # Build list of cuts.
        self.cutsTree = QtGui.QTreeWidget(self)
        self.cutsTree.headerItem().setHidden(True)
        self.tabWidget.addTab(self.cutsTree, self.tr("&Cuts"))
        # Build list of externals.
        self.externalsList = QtGui.QListWidget(self)
        self.tabWidget.addTab(self.externalsList, self.tr("&Exts"))
        # Build list of function templates.
        self.functionsList = QtGui.QListWidget(self)
        self.functionsList.addItems([name for name, _ in self.Functions])
        self.tabWidget.addTab(self.functionsList, self.tr("&Funcs"))
        # Build list of operators.
        self.operatorsList = QtGui.QListWidget(self)
        self.operatorsList.addItems([name for name, _ in self.Operators])
        self.tabWidget.addTab(self.operatorsList, self.tr("O&ps"))
        # Insert button.
        self.insertButton = QtGui.QPushButton(Toolbox.createIcon("insert-text"), self.tr("&Insert"), self)
        self.insertButton.clicked.connect(self.onInsert)
        self.insertButton.setDefault(False)
        # Wizard option.
        self.wizardCheckBox = QtGui.QCheckBox(self.tr("Use &wizard"), self)
        # Preview widget.
        self.previewLabel = QtGui.QTextEdit(self)
        self.previewLabel.setReadOnly(True)
        # Create list contents.
        self.initContents()
        # Layout
        gridLayout = QtGui.QGridLayout()
        gridLayout.setContentsMargins(1, 1, 1, 1)
        gridLayout.addWidget(self.filterBar, 0, 0, 1, 3)
        gridLayout.addWidget(self.tabWidget, 1, 0, 1, 3)
        gridLayout.addWidget(self.insertButton, 2, 0)
        gridLayout.addWidget(self.wizardCheckBox, 2, 1)
        gridLayout.addWidget(self.previewLabel, 3, 0, 1, 3)
        self.setLayout(gridLayout)
        # Setup connections.
        self.objectsTree.currentItemChanged.connect(self.onPreview)
        self.objectsTree.itemDoubleClicked.connect(self.onInsert)
        self.cutsTree.currentItemChanged.connect(self.onPreview)
        self.cutsTree.itemDoubleClicked.connect(self.onInsert)
        self.externalsList.currentRowChanged.connect(self.onPreview)
        self.externalsList.itemDoubleClicked.connect(self.onInsert)
        self.functionsList.currentRowChanged.connect(self.onPreview)
        self.functionsList.itemDoubleClicked.connect(self.onInsert)
        self.operatorsList.selectionModel().currentRowChanged.connect(self.onPreview)
        self.operatorsList.doubleClicked.connect(self.onInsert)
        self.tabWidget.currentChanged.connect(self.onPreview)

    def initContents(self):
        """Populate library lists with content from menu."""
        # Build list of objects.
        self.objectsTree.clear()
        topLevelItems = {}
        for object in sorted(self.menu.objects): # Applies custom sort of class
            icon = QtGui.QIcon()
            if object.type in (tmGrammar.MU, ):
                icon.addPixmap(miniIcon("mu"))
            if object.type in (tmGrammar.EG, ):
                icon.addPixmap(miniIcon("eg"))
            if object.type in (tmGrammar.TAU, ):
                icon.addPixmap(miniIcon("tau"))
            if object.type in (tmGrammar.JET, ):
                icon.addPixmap(miniIcon("jet"))
            if object.type in (tmGrammar.ETT, tmGrammar.HTT, tmGrammar.ETM, tmGrammar.HTM, tmGrammar.ETTEM, tmGrammar.ETMHF):
                icon.addPixmap(miniIcon("esums"))
            if not object.type in topLevelItems.keys():
                item = QtGui.QTreeWidgetItem(self.objectsTree, [object.type])
                item.setIcon(0, icon)
                topLevelItems[object.type] = item
            item = QtGui.QTreeWidgetItem(topLevelItems[object.type], [object.name])
            item.setIcon(0, icon)
        # Build list of cuts.
        self.cutsTree.clear()
        topLevelItems = {}
        for cut in sorted(self.menu.cuts): # Applies custom sort of class
            if not cut.object in topLevelItems.keys():
                if cut.object not in (tmGrammar.comb, tmGrammar.mass):
                    topLevelItems[cut.object] = QtGui.QTreeWidgetItem(self.cutsTree, [cut.object])
            if not (cut.object, cut.type) in topLevelItems.keys():
                if cut.object in (tmGrammar.comb, tmGrammar.mass):
                    topLevelItems[(cut.object, cut.type)] = QtGui.QTreeWidgetItem(self.cutsTree, [cut.type])
                else:
                    topLevelItems[(cut.object, cut.type)] = QtGui.QTreeWidgetItem(topLevelItems[cut.object], [cut.type])
            item = QtGui.QTreeWidgetItem(topLevelItems[(cut.object, cut.type)], [cut.name])
        # Build list of externals.
        self.externalsList.clear()
        names = [external.name for external in self.menu.externals]
        names += ['EXT_' + external['name'] for external in self.menu.extSignals.extSignals]
        names = sorted(set(names))
        self.externalsList.addItems(names)
        # Refresh UI.
        self.onPreview()
        # Default message.
        self.previewLabel.setText(self.tr("""
            <img src=\"/usr/share/icons/gnome/16x16/actions/help-about.png\"/>
            <strong>Double click</strong> on an above item to insert it at the current
            cursor position or click on the <strong><img src=\"/usr/share/icons/gnome/16x16/actions/insert-text.png\"/> Insert</strong> button.
        """))


    def onPreview(self):
        """Updates preview widget with current selected library item."""
        self.previewLabel.setText("")
        self.insertButton.setEnabled(False)
        self.wizardCheckBox.setEnabled(False)
        tab = self.tabWidget.currentWidget()
        # Objects
        if tab == self.objectsTree:
            if not self.objectsTree.currentItem(): return # empty list
            item = self.menu.objectByName(self.objectsTree.currentItem().text(0))
            # self.wizardCheckBox.setEnabled(True)
            if not item: return
            item = dict(**item) # Copy
            item['threshold'] = Toolbox.fThreshold(item['threshold'])
            item['bx_offset'] = Toolbox.fBxOffset(item['bx_offset'])
            self.previewLabel.setText(self.ObjectPreview.format(**item))
            self.insertButton.setEnabled(True)
            self.wizardCheckBox.setEnabled(True)
        # Cuts
        elif tab == self.cutsTree:
            if not self.cutsTree.currentItem(): return # empty list
            item = self.menu.cutByName(self.cutsTree.currentItem().text(0))
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
            self.insertButton.setEnabled(True)
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
            self.wizardCheckBox.setEnabled(True)
            if row < 0: return
            self.previewLabel.setText(self.Operators[row][1])
            self.insertButton.setEnabled(True)

    def onInsert(self):
        """Insert selected item from active library list."""
        if self.insertButton.isEnabled():
            widget = self.tabWidget.currentWidget()
            item = widget.currentItem()
            if widget is self.objectsTree:
                    if self.wizardCheckBox.isChecked():
                        dialog = ObjectEditorDialog(self.menu, self)
                        dialog.loadObject(item.text(0))
                        dialog.exec_()
                        self.selected.emit(dialog.toExpression())
                        return
            if isinstance(widget, QtGui.QTreeWidget):
                self.selected.emit(item.text(0))
                return
            if isinstance(widget, QtGui.QListWidget):
                self.selected.emit(item.text())
                return

# helper
def currentData(widget):
    rows = widget.selectionModel().selectedRows()
    if rows:
        return rows[0].data().toPyObject()
    return

# -----------------------------------------------------------------------------
#  Index selection dialog.
# -----------------------------------------------------------------------------

class AlgorithmSelectionDialog(QtGui.QDialog):
    """Dialog for graphical selection of algorithm index.
    Displays a colored button grid representing all available index slots.
    Already used indexes are colored red, free are colored green. User can assign
    an index by clicking a free index button.
    """
    # Define size of the index grid.
    ColumnCount = 16
    RowCount    = MaxAlgorithms // ColumnCount

    def __init__(self, index, reserved, parent = None):
        super(AlgorithmSelectionDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Select Index"))
        self.resize(590, 300)
        self.index = index
        # Button box with cancel button
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.buttonBox.button(QtGui.QDialogButtonBox.Cancel).setAutoDefault(False)
        self.buttonBox.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        # Layout to add Buttons
        gridLayout = QtGui.QGridLayout()
        gridLayout.setHorizontalSpacing(2)
        gridLayout.setVerticalSpacing(2)
        self.gridWidget = QtGui.QWidget(self)
        # Create a scroll area for the preview
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        # Variable to iterate over all indices.
        index = 0
        # Add items to the grid in the scroll area
        for row in range(self.RowCount):
            for column in range(self.ColumnCount):
                if index >= MaxAlgorithms:
                    break
                button = QtGui.QPushButton(str(index), self)
                button.setCheckable(True)
                button.setFixedSize(30, 30)
                button.clicked[bool].connect(self._updateIndex)
                gridLayout.addWidget(button, row, column)
                if index in reserved:
                    # if index is not available, button can not be clicked
                    button.setEnabled(False)
                    button.setChecked(True)
                if index == self.index:
                    # In Edition-Action Original Index is always enabled
                    button.setChecked(True)
                    self.currentButton = button
                # Increment index.
                index += 1
        # Layout for Dailog Window
        self.gridWidget.setLayout(gridLayout)
        self.scrollArea.setWidget(self.gridWidget)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.scrollArea)
        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.addWidget(Toolbox.IconLabel(Toolbox.createIcon("info"), self.tr("Select a free algorithm index."), self))
        bottomLayout.addWidget(self.buttonBox)
        layout.addLayout(bottomLayout)
        self.setLayout(layout)
        self.scrollArea.ensureWidgetVisible(self.currentButton)

    def _updateIndex(self):
        """Get new index from the button."""
        self.index = int(str(self.sender().text())) # From QString to integer.
        self.accept()

if __name__ == '__main__':
    import sys
    from tmEditor import Menu
    app = QtGui.QApplication(sys.argv)
    menu = Menu(sys.argv[1])
    window = AlgorithmEditorDialog(menu)
    window.show()
    sys.exit(app.exec_())
