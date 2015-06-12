# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

class AlgorithmFormatter(object):
    """Formatter class used to format user input to the (currently very)
    restrictive algorithm equation syntax.
    """
    def machinize(self, algorithm):
        for keyword in ("AND", "OR", "XOR", "NOT", "(", ")", "[", "]", "{", "}", ",", ):
            algorithm = algorithm.replace(keyword, " {keyword} ".format(keyword = keyword))
        algorithm = ' '.join(algorithm.split())
        # TODO: now that's way not the best approach at all, use regular expressions instead...
        algorithm = algorithm.replace(" , ", ",")
        algorithm = algorithm.replace(" ( ", "(")
        algorithm = algorithm.replace(" )", ")")
        algorithm = algorithm.replace(" [ ", "[")
        algorithm = algorithm.replace(" ]", "]")
        algorithm = algorithm.replace(" { ", "{")
        algorithm = algorithm.replace(" }", "}")
        for keyword in ("AND", "OR", "XOR", "NOT", ):
            algorithm = algorithm.replace(keyword, " {keyword} ".format(keyword = keyword))
        return algorithm.replace("  ", " ") # TODO: that's not efficient...
    def humanize(self, algorithm):
        algorithm = self.machinize(algorithm)
        algorithm = algorithm.replace(",", ", ")
        return algorithm
    def expanded(self, algorithm):
        algorithm = self.machinize(algorithm)
        # TODO: now that's way not the best approach at all, use regular expressions instead...
        algorithm = algorithm.replace("{", "{\n  ")
        algorithm = algorithm.replace("}", "\n}")
        algorithm = algorithm.replace("[", "[\n  ")
        algorithm = algorithm.replace("]", "\n]")
        algorithm = algorithm.replace("(", "(\n  ")
        algorithm = algorithm.replace(")", "\n)")
        algorithm = algorithm.replace(",", ",\n  ")
        return algorithm
