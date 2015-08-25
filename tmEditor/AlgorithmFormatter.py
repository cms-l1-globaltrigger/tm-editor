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
    Paranthesis = ('(', ')', '{', '}', '[', ']', )
    Separators = (',', )
    def machinize(self, algorithm):
        """Return expression applying strict foramtting required by tmGrammar classes."""
        def separate(keyword, algorithm):
            """Embraces a token with spaces."""
            return algorithm.replace(keyword, " {keyword} ".format(keyword = keyword))
        for keyword in self.Functions:
            algorithm = separate(keyword, algorithm)
        for keyword in self.Paranthesis:
            algorithm = separate(keyword, algorithm)
        for keyword in self.Separators:
            algorithm = separate(keyword, algorithm)
        for keyword in self.Operators:
            algorithm = algorithm.replace(" {keyword} ", " {keyword} ".format(keyword = keyword))
        algorithm = ' '.join(algorithm.split())
        # TODO: now that's way not the best approach at all, use regular expressions instead...
        algorithm = algorithm.replace(" , ", ",")
        algorithm = algorithm.replace("( ", "(")
        algorithm = algorithm.replace(" )", ")")
        algorithm = algorithm.replace(" [ ", "[")
        algorithm = algorithm.replace(" ]", "]")
        algorithm = algorithm.replace(" { ", "{")
        algorithm = algorithm.replace(" }", "}")
        for keyword in self.Operators:
            algorithm = algorithm.replace(keyword, keyword)
            algorithm = algorithm.replace(keyword.lower(), keyword)
        return algorithm.replace("  ", " ") # TODO: that's not efficient...
    def humanize(self, algorithm):
        """Returns expression applying a human readable formatting."""
        algorithm = self.machinize(algorithm)
        algorithm = algorithm.replace(",", ", ")
        return algorithm
    def expanded(self, algorithm):
        """Return expression applying an expanding formatting."""
        algorithm = self.machinize(algorithm)
        # TODO: now that's way not the best approach at all, use regular expressions instead...
        algorithm = algorithm.replace(",", ", ")
        temp = []
        i = 0
        level = 0
        while i < len(algorithm):
            if algorithm[i].startswith('('):
                level += 1
                temp.append(algorithm[i])
                temp.append(EOL)
                temp.append(INDENT * level)
                i += 1
            elif algorithm[i:i+2].startswith(tmGrammar.OR):
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(algorithm[i:i+2])
                temp.append(EOL)
                temp.append(INDENT * level)
                i += 3
            elif algorithm[i:i+3].startswith(tmGrammar.AND):
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(algorithm[i:i+3])
                temp.append(EOL)
                temp.append(INDENT * level)
                i += 4
            elif algorithm[i:i+3].startswith(tmGrammar.XOR):
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(algorithm[i:i+3])
                temp.append(EOL)
                temp.append("  " * (level))
                i += 4
            elif algorithm[i].startswith(')'):
                if level: level -= 1
                temp.append(EOL)
                temp.append(INDENT * level)
                temp.append(algorithm[i])
                i += 1
            else:
                temp.append(algorithm[i])
                i += 1

        # algorithm = temp
        return ''.join(temp)
