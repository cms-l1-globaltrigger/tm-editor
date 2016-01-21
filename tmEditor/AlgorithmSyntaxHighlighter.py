# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm syntax highlighter class.
"""

import tmGrammar

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from collections import namedtuple

__all__ = ['AlgorithmSyntaxHighlighter', ]

def makeKeyword(key):
    return "\\b{key}\\b".format(key = key)

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
        keywordPatterns = [
            makeKeyword(tmGrammar.AND),
            makeKeyword(tmGrammar.OR),
            makeKeyword(tmGrammar.XOR),
            makeKeyword(tmGrammar.NOT),
        ]
        for pattern in keywordPatterns:
            self.highlightingRules.append(
                self.HighlightingRule(keywordFormat, QRegExp(pattern)))
        functionFormat = QTextCharFormat()
        functionFormat.setForeground(Qt.blue)
        functionFormat.setFontWeight(QFont.Bold)
        rule = self.HighlightingRule(functionFormat,
            QRegExp("\\b{tmGrammar.comb}|{tmGrammar.dist}|{tmGrammar.mass}+(?=\\{{)".format(tmGrammar = tmGrammar)))
        self.highlightingRules.append(rule)

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = expression.indexIn(text, index + length)
