# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm editor window.
"""

from tmEditor import AlgorithmFormatter
from tmEditor import Toolbox

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from collections import namedtuple
import sys, os

class AlgorithmEditor(QMainWindow):
    def __init__(self, algorithm, menu = Toolbox.L1MenuContainer(), parent = None):
        super(AlgorithmEditor, self).__init__(parent)
        # Setup window
        self.setWindowTitle(self.tr("Algorithm Editor"))
        self.resize(720, 480)
        # Setup helper
        self.menu = menu
        self.formatter = AlgorithmFormatter()
        # Create actions and toolbars.
        self.createActions()
        self.createMenus()
        self.createToolbar()
        # Setup widgets
        self.textEdit = QTextEdit(self)
        font = self.textEdit.font()
        font.setFamily("Monospace")
        self.textEdit.setFont(font)
        self.textEdit.setFrameShape(QFrame.NoFrame)
        self.textEdit.setCursorWidth(2)
        self.setAlgorithm(algorithm)
        self.highlighter = SyntaxHighlighter(self.textEdit)
        # Setup layout
        # gridLayout = QGridLayout()
        # gridLayout.addWidget(self.textEdit, 0, 0)
        # centralWidget = QWidget(self)
        # centralWidget.setLayout(gridLayout)
        self.setCentralWidget(self.textEdit)
        # Setup dock widgets
        dock = QDockWidget(self.tr("Library"), self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.libraryWidget = LibraryWidget(self.menu, dock)
        self.libraryWidget.insertItem.connect(self.insertItem)
        dock.setWidget(self.libraryWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def insertItem(self, text):
        self.textEdit.textCursor().insertText(text)
        self.textEdit.ensureCursorVisible()

    def createActions(self):
        self.formatCompactAct = QAction(self.tr("&Compact"), self)
        self.formatCompactAct.triggered.connect(self.onFormatCompact)
        self.formatExpandAct = QAction(self.tr("&Expand"), self)
        self.formatExpandAct.triggered.connect(self.onFormatExpand)

    def createMenus(self):
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.formatMenu = self.menuBar().addMenu(self.tr("&Format"))
        self.formatMenu.addAction(self.formatCompactAct)
        self.formatMenu.addAction(self.formatExpandAct)
        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))

    def createToolbar(self):
        pass

    def algorithm(self):
        """Returns a machine readable formatted version of the loaded algorithm."""
        return self.formatter.machinize(str(self.textEdit.toPlainText()))

    def setAlgorithm(self, algorithm):
        self.textEdit.setPlainText(self.formatter.humanize(algorithm))

    def onFormatCompact(self):
        self.textEdit.setPlainText(self.formatter.humanize(self.algorithm()))

    def onFormatExpand(self):
        self.textEdit.setPlainText(self.formatter.expanded(self.algorithm()))

    def reloadLibrary(self):
        self.libraryWidget.reloadMenu()

class SyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highighter class for algorithm equations."""
    HighlightingRule = namedtuple('HighlightingRule', 'format, pattern')
    def __init__(self, document):
        """Attribute *document* requires a text document instance or a text
        edit widget instance to apply syntax highlighting on.
        """
        super(SyntaxHighlighter, self).__init__(document)
        self.highlightingRules = []
        # Keywords: AND, OR, XOR, NOT
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.darkBlue)
        keywordFormat.setFontWeight(QFont.Bold)
        keywordPatterns = QStringList()
        keywordPatterns << "\\bAND\\b" << "\\bOR\\b" << "\\bXOR\\b" << "\\bNOT\\b"
        for pattern in keywordPatterns:
            self.highlightingRules.append(
                self.HighlightingRule(keywordFormat, QRegExp(pattern)))
        functionFormat = QTextCharFormat()
        functionFormat.setForeground(Qt.blue)
        functionFormat.setFontWeight(QFont.Bold)
        rule = self.HighlightingRule(functionFormat, QRegExp("\\bcomb|delta|mass+(?=\\{)"))
        self.highlightingRules.append(rule)
    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = expression.indexIn(text, index + length)

class LibraryWidget(QWidget):
    insertItem = pyqtSignal(str)
    def __init__(self, menu, parent = None):
        super(LibraryWidget, self).__init__(parent)
        self.menu = menu
        self.tabWidget = QTabWidget(self)
        # Build list of objects.
        self.objectsList = QListWidget(self)
        # Build list of cuts.
        self.tabWidget.addTab(self.objectsList, "&Objects")
        self.cutsList = QListWidget(self)
        # Build list of function templates.
        self.tabWidget.addTab(self.cutsList, "&Cuts")
        self.functionsList = QListWidget(self)
        self.functionsList.addItems([
            "comb{obj, obj}",
            "comb{obj, obj, obj}",
            "comb{obj, obj, obj, obj}",
            "dist{obj, obj}[cut]",
            "dist{obj, obj}[cut, cut]",
            "mass{obj, obj}[cut]",
        ])
        self.tabWidget.addTab(self.functionsList, "&Functions")
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
        self.functionsList.itemDoubleClicked.connect(self.insertFunction)
        self.tabWidget.currentChanged.connect(self.setPreview)

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
        # TODO clean up, not effective
        row = self.objectsList.currentRow()
        self.insertItem.emit(self.menu.objects[row]['name'])

    def insertCut(self):
        # TODO clean up, not effective
        row = self.cutsList.currentRow()
        self.insertItem.emit(self.menu.cuts[row]['name'])

    def insertFunction(self):
        # TODO clean up, not effective
        self.insertItem.emit(self.functionsList.currentItem().text())

    def reloadMenu(self):
        # TODO clean up
        # Build list of objects.
        self.objectsList.clear()
        self.objectsList.addItems([obj['name'] for obj in self.menu.objects])
        # Build list of cuts.
        self.cutsList.clear()
        self.cutsList.addItems([cut['name'] for cut in self.menu.cuts])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AlgorithmEditor(sys.argv[1] if len(sys.argv) > 1 else "MU10 AND MU20[PHI_TOP] OR comb{MU10, MU20}")
    window.show()
    sys.exit(app.exec_())
