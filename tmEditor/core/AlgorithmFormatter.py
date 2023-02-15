"""Algorithm expression formatter.

Compress an algorithm expression before assining it to tmGrammar functions:

>>> AlgorithmFormatter.compress(expression)

Normalize an algorithm expression optimized for human readability:

>>> AlgorithmFormatter.normalize(expression)

Cascade an algorithm expression to increase human readability:

>>> AlgorithmFormatter.expand(expression)
"""

from typing import List, Optional

import tmGrammar

from .types import FunctionTypes

__all__ = ['AlgorithmFormatter', ]


class AlgorithmFormatter:
    """Formatter class used to format user input to the (currently very)
    restrictive algorithm equation syntax.
    """

    Functions = FunctionTypes
    Negators = (tmGrammar.NOT, )
    Operators = (tmGrammar.AND, tmGrammar.OR, tmGrammar.XOR, ) + Negators
    LeftPar = '('
    RightPar = ')'
    LeftFunctionPar = '{'
    RightFunctionPar = '}'
    LeftCutPar = '['
    RightCutPar = ']'
    OpeningPar = (LeftPar, LeftFunctionPar, LeftCutPar, )
    ClosingPar = (RightPar, RightFunctionPar, RightCutPar, )
    Paranthesis = OpeningPar + ClosingPar
    Separators = (',', )
    Spaces = (' ', '\t', '\r', '\n')

    @staticmethod
    def tokenize(expression: str) -> List[str]:
        """Robust algorithm expression tokenization, splitting expression in
        objects, functions, cuts and paranthesis.

        >>> tokenize("comb{MU20[MU-ISO_1],MU10}")
        ['comb', '{', 'MU20', '[', 'MU-ISO_1', ']', ',', 'MU10', '}']
        """
        tokens: List[str] = []
        token: List[str] = []
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
    def sanitize(expression: str) -> List[str]:
        """Returns sanitized tokens auto correcting some frequent mistakes, like
        lower case operators, upper case function names, and removes occurences
        of multiple commas and trailing commas.

        >>> tokens = sanitize("MU10 and COMB{JET20, ,JET10, }")
        ['MU10', 'AND', 'comb', '{', 'JET20', ',', 'JET10', '}']
        """
        tokens: List[str] = []
        for token in AlgorithmFormatter.tokenize(expression):
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
            elif token in AlgorithmFormatter.ClosingPar:
                if tokens and tokens[-1] in AlgorithmFormatter.Separators:
                    tokens = tokens[:-1]
            tokens.append(token)
        return tokens

    @staticmethod
    def compress(expression: str) -> str:
        """Return expression applying strict foramtting required by tmGrammar.

        >>> compress("comb{MU40, MU30, MU20, MU10, }")
        'comb{MU40,MU30,MU20,MU10}'
        """
        tokens = []
        for token in AlgorithmFormatter.sanitize(expression):
            if token in AlgorithmFormatter.Operators:
                token = " {token} ".format(token=token)
            tokens.append(token)
        return ''.join(tokens)

    @staticmethod
    def normalize(expression: str) -> str:
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
    def expand(expression: str, tabwidth: int = 2, ws: Optional[str] = None, eol: Optional[str] = None) -> str:
        """Return expression applying an expanded formatting.

        >>> print expand("MU10 AND (JET20 OR TAU20)")
        MU10
         AND (
          JET20
           OR
          TAU20
        )
        """
        ws = ws or " "
        eol = eol or "\n"
        level = 0
        # Returns indent according to current
        def indent():
            return ws * tabwidth * level
        result: List[str] = []
        previous = None
        # Track paranthesis levels.
        in_function = False
        in_cut = False

        negator = tmGrammar.NOT
        lpars = (AlgorithmFormatter.LeftPar, AlgorithmFormatter.LeftFunctionPar, )
        rpars = (AlgorithmFormatter.RightPar, AlgorithmFormatter.RightFunctionPar, )

        for token in AlgorithmFormatter.sanitize(expression):
            # Update states
            if token == AlgorithmFormatter.LeftFunctionPar:
                in_function = True
            elif token == AlgorithmFormatter.RightFunctionPar:
                in_function = False
            elif token == AlgorithmFormatter.LeftCutPar:
                in_cut = True
            elif token == AlgorithmFormatter.RightCutPar:
                in_cut = False
            # Increase indentation level
            if token in rpars:
                level -= 1
            #
            if token in AlgorithmFormatter.Negators:
                if previous in AlgorithmFormatter.Operators:
                    result += (eol, indent(), )
                result += (token, )
            elif token in AlgorithmFormatter.Operators:
                if previous != AlgorithmFormatter.LeftPar:
                    result += (eol, ws, token)
                else:
                    result += (token, )
            elif token == AlgorithmFormatter.LeftPar:
                result += (ws if previous else '', token, eol, indent(), ws*tabwidth)
            elif token in lpars:
                result += (ws if previous not in AlgorithmFormatter.Functions else '', token)
            elif token in rpars:
                result += (eol if previous else '', indent(), token)
            else:
                if previous == AlgorithmFormatter.RightPar:
                    result += (ws, token)
                elif previous == AlgorithmFormatter.LeftPar:
                    result += (token, )
                elif previous in lpars:
                    result += (eol, indent(), token)
                elif previous == negator:
                    result += (ws, token)
                elif previous in AlgorithmFormatter.Operators:
                    result += (eol, indent(), token)
                else:
                    result += (token, )
            # Reduce indentation level
            if token in lpars:
                level += 1
            # Separate after commas inside functions
            if token in AlgorithmFormatter.Separators:
                if in_function and not in_cut:
                    result += (eol, indent(), )
                else:
                    result += (ws, )
            previous = token

        return ''.join(result)
