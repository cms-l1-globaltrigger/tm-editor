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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from collections import namedtuple
import sys, os

class AlgorithmEditor(QMainWindow):
    def __init__(self, algorithm, parent = None):
        super(AlgorithmEditor, self).__init__(parent)
        # Setup window
        self.setWindowTitle(self.tr("Algorithm Editor"))
        self.resize(640, 480)
        # Setup helper
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
        self.textEdit.setPlainText(self.formatter.humanize(algorithm))
        self.highlighter = SyntaxHighlighter(self.textEdit)
        # Setup layout
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.textEdit, 0, 0)
        centralWidget = QWidget(self)
        centralWidget.setLayout(gridLayout)
        self.setCentralWidget(centralWidget)
        # Setup dock widgets
        dock = QDockWidget(self.tr("Cuts"), self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        customerList = QListWidget(dock)
        customerList.addItems(QStringList()
             << "MU-PHI_TOP"
             << "MU-PHI_BOTTOM"
             << "EG-PHI_TOP"
             << "JET-ETA_FORWARD"
             << "JET-PHI_MANGLE"
             << "JET-PHI_TOP_L2PR")
        dock.setWidget(customerList)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

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

    def onFormatCompact(self):
        self.textEdit.setPlainText(self.formatter.humanize(self.algorithm()))

    def onFormatExpand(self):
        self.textEdit.setPlainText(self.formatter.expanded(self.algorithm()))

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AlgorithmEditor(sys.argv[1] if len(sys.argv) > 1 else "MU10 AND MU20[PHI_TOP] OR comb{MU10, MU20}")
    window.show()
    sys.exit(app.exec_())
