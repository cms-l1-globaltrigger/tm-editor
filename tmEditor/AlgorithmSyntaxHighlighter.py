# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm syntax highlighter class.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from collections import namedtuple

__all__ = ['AlgorithmSyntaxHighlighter', ]

class AlgorithmSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highighter class for algorithm expressions."""
    HighlightingRule = namedtuple('HighlightingRule', 'format, pattern')
    def __init__(self, document):
        """Attribute *document* requires a text document instance or a text
        edit widget instance to apply syntax highlighting on.
        """
        super(AlgorithmSyntaxHighlighter, self).__init__(document)
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
