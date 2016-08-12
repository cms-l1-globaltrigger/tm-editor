# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm syntax highlighter derived from QtGui.QSyntaxHighlighter class,
 to be attached to an QtGui.QDocument instance.

Usage example
-------------

Attaching a syntax hilighter to an text document is quite simple:

>>> editor = QtGui.QPlainTextEdit()
>>> AlgorithmSyntaxHighlighter(editor.document())

"""

import tmGrammar

from PyQt4 import QtCore
from PyQt4 import QtGui

from collections import namedtuple

__all__ = ['AlgorithmSyntaxHighlighter', ]

def makeKeyword(key):
    return "\\b{key}\\b".format(key = key)

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
        functionFormat = QtGui.QTextCharFormat()
        functionFormat.setForeground(QtCore.Qt.blue)
        functionFormat.setFontWeight(QtGui.QFont.Bold)
        rule = self.HighlightingRule(functionFormat,
            QtCore.QRegExp("\\b{tmGrammar.comb}|{tmGrammar.dist}|{tmGrammar.mass}+(?=\\{{)".format(tmGrammar = tmGrammar)))
        self.highlightingRules.append(rule)

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = QtCore.QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = expression.indexIn(text, index + length)
