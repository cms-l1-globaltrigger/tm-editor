# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm expression formatter.

Compress an algorithm expression before assining it to tmGrammar functions:

>>> AlgorithmFormatter.compress(expression)

Normalize an algorithm expression optimized for human readability:

>>> AlgorithmFormatter.normalize(expression)

Cascade an algorithm expression to increase human readability:

>>> AlgorithmFormatter.expand(expression)
"""

import tmGrammar

__all__ = ['AlgorithmFormatter', ]

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

    @staticmethod
    def tokenize(expression):
        """Robust algorithm expression tokenization, splitting expression in
        objects, functions, cuts and paranthesis.

        >>> tokenize("comb{MU20[MU-ISO_1],MU10}")
        ['comb', '{', 'MU20', '[', 'MU-ISO_1', ']', ',', 'MU10', '}']
        """
        tokens = []
        token = []
        for char in expression:
            # Ignore spaces, append optional previous token.
            if char in AlgorithmFormatter.Spaces:
                if token:
                    tokens.append(''.join(token))
                token = []
            # Append optional previous token, append separator.
            elif char in AlgorithmFormatter.Separators or \
                 char in AlgorithmFormatter.Paranthesis:
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

    @staticmethod
    def sanitize(expression):
        """Returns sanitized tokens auto correcting some frequent mistakes, like
        lower case operators, upper case function names, and removes occurences
        of multiple commas and trailing commas.

        >>> tokens = sanitize("MU10 and COMB{JET20, ,JET10, }")
        ['MU10', 'AND', 'comb', '{', 'JET20', ',', 'JET10', '}']
        """
        tokens = []
        for i, token in enumerate(AlgorithmFormatter.tokenize(expression)):
            # Make sure operators are upper case.
            if token.upper() in AlgorithmFormatter.Operators:
                token = token.upper()
            # Make sure function names are lower case.
            elif token.lower() in AlgorithmFormatter.Functions:
                token = token.lower()
            # Remove multiple commas.
            elif token in AlgorithmFormatter.Separators:
                if tokens and tokens[-1] in AlgorithmFormatter.Separators:
                    tokens = tokens[:-1]
            # Remove trailing commas.
            elif token in AlgorithmFormatter.ClosingParanthesis:
                if tokens and tokens[-1] in AlgorithmFormatter.Separators:
                    tokens = tokens[:-1]
            tokens.append(token)
        return tokens

    @staticmethod
    def compress(expression):
        """Return expression applying strict foramtting required by tmGrammar.

        >>> compress("comb{MU40, MU30, MU20, MU10, }")
        'comb{MU40,MU30,MU20,MU10}'
        """
        tokens = []
        for i, token in enumerate(AlgorithmFormatter.sanitize(expression)):
            if token in AlgorithmFormatter.Operators:
                token = " {token} ".format(token = token)
            tokens.append(token)
        return ''.join(tokens)

    @staticmethod
    def normalize(expression):
        """Returns expression applying a human readable formatting.

        >>> normalize("comb{MU40,MU30,MU20,MU10}")
        'comb{MU40, MU30, MU20, MU10}'
        """
        expression = AlgorithmFormatter.compress(expression)
        rules = ((",", ", "), ("(", " ( "), (")", " ) "), ("  ", " "), )
        for src, dst in rules:
            expression = expression.replace(src, dst)
        return expression.strip()

    @staticmethod
    def expand(expression, tabwidth = 2, ws = " ", eol = "\n"):
        """Return expression applying an expanded formatting.

        >>> print expand("MU10 AND (JET20 OR TAU20)")
        MU10
         AND
        (
          JET20
           OR
          TAU20
        )
        """
        tokens = AlgorithmFormatter.sanitize(expression)
        level = 0
        result = []
        previous = None
        def indent(): return ws * tabwidth * level
        for token in tokens:
            if token == ')':
                level -= 1
            if token in (tmGrammar.AND, tmGrammar.OR, tmGrammar.XOR):
                result += (eol, indent(), ws, token)
            elif token in ('(', ')'):
                result += (eol if previous else '', indent(), token)
            else:
                if previous in ('(', ):
                    result += (eol, indent(), token)
                elif previous in (tmGrammar.AND, tmGrammar.OR, tmGrammar.XOR):
                    result += (eol, indent(), token)
                elif previous in (tmGrammar.NOT, ):
                    result += (ws, token)
                else:
                    result += (token, )
            if token == '(':
                level += 1
            previous = token
            # Separate after commas
            if token == ',':
                result += (ws, )

        return ''.join(result)
