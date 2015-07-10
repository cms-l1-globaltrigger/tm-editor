# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm formatter class.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['AlgorithmFormatter', ]

class AlgorithmFormatter(object):
    """Formatter class used to format user input to the (currently very)
    restrictive algorithm equation syntax.
    """
    Functions = ('comb', 'delta', 'mass', )
    Operators = ('AND', 'OR', 'XOR', 'NOT', )
    Paranthesis = ('(', ')', '{', '}', '[', ']', )
    Separators = (',', )
    def free(self, token):
        return " {0} ".format(token)
    def machinize(self, algorithm):
        def separate(keyword, algorithm):
            return algorithm.replace(keyword, " {keyword} ".format(keyword = keyword))
        for keyword in self.Functions:
            algorithm = separate(keyword, algorithm)
        for keyword in self.Operators:
            algorithm = separate(keyword, algorithm)
        for keyword in self.Paranthesis:
            algorithm = separate(keyword, algorithm)
        for keyword in self.Separators:
            algorithm = separate(keyword, algorithm)
        algorithm = ' '.join(algorithm.split())
        # TODO: now that's way not the best approach at all, use regular expressions instead...
        algorithm = algorithm.replace(" , ", ",")
        algorithm = algorithm.replace(" ( ", "(")
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
        algorithm = self.machinize(algorithm)
        algorithm = algorithm.replace(",", ", ")
        return algorithm
    def expanded(self, algorithm):
        algorithm = self.machinize(algorithm)
        # TODO: now that's way not the best approach at all, use regular expressions instead...
        # algorithm = algorithm.replace("{", "{\n  ")
        # algorithm = algorithm.replace("}", "\n}")
        # algorithm = algorithm.replace("[", "[\n  ")
        # algorithm = algorithm.replace("]", "\n]")
        # algorithm = algorithm.replace("(", "(\n  ")
        # algorithm = algorithm.replace(")", "\n)")
        # algorithm = algorithm.replace(",", ",\n  ")
        algorithm = algorithm.replace(" AND ", "\n AND \n")
        algorithm = algorithm.replace(" OR ", "\n OR \n")
        algorithm = algorithm.replace(" XOR ", "\n XOR \n")
        return algorithm
