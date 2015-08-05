# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm syntax validator class.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['AlgorithmSyntaxValidator', ]

class SyntaxValidator(object):

    def __init__(self):
        self.rules = []

    def validate(self, expression):
        for rule in self.rules:
            pass

    def addRule(self, cls):
        self.rules.append(cls())

class AlgorithmSyntaxValidator(SyntaxValidator):

    def __init__(self):
        super(AlgorithmSyntaxValidator, self).__init__()
        self.addRule(CombBxLimit)

class AlgorithmSyntaxRule(object):

    def __init__(self):
        pass

class CombBxLimit(AlgorithmSyntaxRule):

    def __init__(self):
        pass
