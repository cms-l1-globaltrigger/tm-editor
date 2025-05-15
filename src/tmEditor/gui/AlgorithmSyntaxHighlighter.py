"""Algorithm syntax highlighter derived from QtGui.QSyntaxHighlighter class,
 to be attached to an QtGui.QTextDocument instance.

Usage example
-------------

Attaching a syntax hilighter to an text document is quite simple:

>>> editor = QtWidgets.QPlainTextEdit()
>>> AlgorithmSyntaxHighlighter(editor.document())

"""

from collections import namedtuple

from PySide6 import QtCore, QtGui

import tmGrammar

from tmEditor.core.types import FunctionTypes

__all__ = ["AlgorithmSyntaxHighlighter"]


def makeKeyword(key: str, /) -> str:
    return "\\b{key}\\b".format(key=key)


HighlightingRule = namedtuple("HighlightingRule", "format, pattern")
"""Container for highlighting rules."""


class AlgorithmSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highighter class for algorithm expressions."""

    def __init__(self, document) -> None:
        """Attribute *document* requires a text document instance or a text
        edit widget instance to apply syntax highlighting on.
        """
        super().__init__(document)
        self.highlightingRules: list[HighlightingRule] = []
        # Keywords: AND, OR, XOR, NOT
        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtCore.Qt.GlobalColor.darkBlue)
        keywordFormat.setFontWeight(QtGui.QFont.Weight.Bold)
        keywordPatterns = [
            makeKeyword(tmGrammar.AND),
            makeKeyword(tmGrammar.OR),
            makeKeyword(tmGrammar.XOR),
            makeKeyword(tmGrammar.NOT),
        ]
        for pattern in keywordPatterns:
            self.highlightingRules.append(
                HighlightingRule(keywordFormat, QtCore.QRegularExpression(pattern)))
        # Highlight function names
        functionFormat = QtGui.QTextCharFormat()
        functionFormat.setForeground(QtCore.Qt.GlobalColor.blue)
        functionFormat.setFontWeight(QtGui.QFont.Weight.Bold)
        tokens = "|".join(FunctionTypes)
        rule = HighlightingRule(
            functionFormat,
            QtCore.QRegularExpression("\\b{tokens}+(?=\\{{)".format(tokens=tokens))
        )
        self.highlightingRules.append(rule)

    def highlightBlock(self, text: str, /) -> None:
        for rule in self.highlightingRules:
            expression = QtCore.QRegularExpression(rule.pattern)  # TODO?
            matchIterator = expression.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, rule.format)
