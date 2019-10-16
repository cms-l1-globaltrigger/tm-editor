# -*- coding: utf-8 -*-

"""Algorithm syntax highlighter derived from QtGui.QSyntaxHighlighter class,
 to be attached to an QtGui.QTextDocument instance.

Usage example
-------------

Attaching a syntax hilighter to an text document is quite simple:

>>> editor = QtWidgets.QPlainTextEdit()
>>> AlgorithmSyntaxHighlighter(editor.document())

"""

import tmGrammar

from tmEditor.core.types import FunctionTypes

from PyQt5 import QtCore
from PyQt5 import QtGui

from collections import namedtuple

__all__ = ['AlgorithmSyntaxHighlighter', ]

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def makeKeyword(key):
    return "\\b{key}\\b".format(key=key)

# -----------------------------------------------------------------------------
#  Algorithm syntax highlighter class
# -----------------------------------------------------------------------------

class AlgorithmSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highighter class for algorithm expressions."""

    HighlightingRule = namedtuple('HighlightingRule', 'format, pattern')
    """Container for highlighting rules."""

    def __init__(self, document):
        """Attribute *document* requires a text document instance or a text
        edit widget instance to apply syntax highlighting on.
        """
        super(AlgorithmSyntaxHighlighter, self).__init__(document)
        self.highlightingRules = []
        # Keywords: AND, OR, XOR, NOT
        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtCore.Qt.darkBlue)
        keywordFormat.setFontWeight(QtGui.QFont.Bold)
        keywordPatterns = [
            makeKeyword(tmGrammar.AND),
            makeKeyword(tmGrammar.OR),
            makeKeyword(tmGrammar.XOR),
            makeKeyword(tmGrammar.NOT),
        ]
        for pattern in keywordPatterns:
            self.highlightingRules.append(
                self.HighlightingRule(keywordFormat, QtCore.QRegExp(pattern)))
        # Highlight function names
        functionFormat = QtGui.QTextCharFormat()
        functionFormat.setForeground(QtCore.Qt.blue)
        functionFormat.setFontWeight(QtGui.QFont.Bold)
        rule = self.HighlightingRule(functionFormat,
            QtCore.QRegExp("\\b{tokens}+(?=\\{{)".format(tokens="|".join(FunctionTypes))))
        self.highlightingRules.append(rule)

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = QtCore.QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = expression.indexIn(text, index + length)
