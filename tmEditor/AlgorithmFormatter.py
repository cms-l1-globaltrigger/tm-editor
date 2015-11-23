# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm formatter class.
"""

import tmGrammar

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['AlgorithmFormatter', ]

EOL = "\n"
INDENT = "  "

class AlgorithmFormatter(object):
    """Formatter class used to format user input to the (currently very)
    restrictive algorithm equation syntax.
    """
    Functions = (tmGrammar.comb, tmGrammar.dist, tmGrammar.mass, )
    Operators = (tmGrammar.AND, tmGrammar.OR, tmGrammar.XOR, tmGrammar.NOT, )
    OpeningParanthesis = ('(', '{', '[', )
    ClosingParanthesis = (')', '}', ']', )
    Paranthesis = OpeningParanthesis + ClosingParanthesis
    Separators = (',', )
    Spaces = (' ', '\t', '\r', '\n')

    def tokenize(self, expression):
        """Solid algorithm expression tokenization."""
        tokens = []
        token = []
        for char in expression:
            # Ignore spaces, append optional previous token.
            if char in self.Spaces:
                if token:
                    tokens.append(''.join(token))
                token = []
            # Append optional previous token, append separator.
            elif char in self.Separators or char in self.Paranthesis:
                if token:
                    tokens.append(''.join(token))
                tokens.append(char)
                token = []
            # Continue collecting token.
            else:
                token.append(char)
        if token:
            tokens.append(''.join(token))
        return tokens

    def sanitize(self, expression):
        """Returns sanitized tokens auto correcting some frequent mistakes."""
        tokens = []
        for i, token in enumerate(self.tokenize(expression)):
            # Make sure operators ar upper case.
            if token.upper() in self.Operators:
                token = token.upper()
            # Make sure function names are lower case.
            elif token.lower() in self.Functions:
                token = token.lower()
            # Remove multiple commas.
            elif token in self.Separators:
                if tokens and tokens[-1] in self.Separators:
                    tokens = tokens[:-1]
            # Remove trailing commas.
            elif token in self.ClosingParanthesis:
                if tokens and tokens[-1] in self.Separators:
                    tokens = tokens[:-1]
            tokens.append(token)
        return tokens

    def mechanize(self, expression):
        """Return expression applying strict foramtting required by tmGrammar classes."""
        tokens = []
        for i, token in enumerate(self.sanitize(expression)):
            if token in self.Operators:
                token = " {token} ".format(token = token)
            tokens.append(token)
        return ''.join(tokens)

    def humanize(self, expression):
        """Returns expression applying a human readable formatting."""
        expression = self.mechanize(expression)
        expression = expression.replace(",", ", ")
        expression = expression.replace("(", " ( ")
        expression = expression.replace(")", " ) ")
        expression = expression.replace("  ", " ") # Ugh, thats still ugly ;D
        return expression.strip()

    def expanded(self, expression):
        """Return expression applying an expanding formatting."""
        expression = self.mechanize(expression)
        # TODO: now that's way not the best approach at all, use regular expressions instead...
        expression = expression.replace(",", ", ")
        temp = []
        i = 0
        level = 0
        while i < len(expression):
            if expression[i].startswith('('):
                level += 1
                temp.append(expression[i])
                temp.append(EOL)
                temp.append(INDENT * level)
                i += 1
            elif expression[i:i+2].startswith(tmGrammar.OR):
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(expression[i:i+2])
                temp.append(EOL)
                temp.append(INDENT * level)
                i += 3
            elif expression[i:i+3].startswith(tmGrammar.AND):
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(expression[i:i+3])
                temp.append(EOL)
                temp.append(INDENT * level)
                i += 4
            elif expression[i:i+3].startswith(tmGrammar.XOR):
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(expression[i:i+3])
                temp.append(EOL)
                temp.append("  " * (level))
                i += 4
            elif expression[i].startswith(')'):
                if level: level -= 1
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(expression[i])
                i += 1
            else:
                temp.append(expression[i])
                i += 1

        return ''.join(temp)
