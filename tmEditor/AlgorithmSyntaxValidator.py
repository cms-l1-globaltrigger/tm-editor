# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Algorithm syntax validator class.

Usage example
-------------

>>> validator = AlgorithmSyntaxValidator()
>>> validator.validate(expression)

"""

import tmGrammar

from tmEditor.Menu import (
    isOperator,
    isObject,
    isCut,
    isFunction,
    toObject,
    toExternal,
    functionObjects,
    functionCuts,
    functionObjectsCuts,
    objectCuts,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['AlgorithmSyntaxValidator', ]

# -----------------------------------------------------------------------------
#  Base classes
# -----------------------------------------------------------------------------

class SyntaxValidator(object):
    """Base class to be inherited by custom syntax validator classes."""

    def __init__(self):
        self.rules = []

    def validate(self, expression):
        for rule in self.rules:
            rule.validate(expression)

    def addRule(self, cls):
        """Add a syntx rule class. Creates and tores an instance of the class."""
        self.rules.append(cls())

class SyntaxRule(object):
    """Base class to be inherited by custom syntax rule classes."""

    def validate(self, expression):
        raise NotImplementedError()

# -----------------------------------------------------------------------------
#  Algorithm language specific classes
# -----------------------------------------------------------------------------

class AlgorithmSyntaxError(Exception):
    """Exeption for algoithm syntax errors thrown by class AlgorithmSyntaxValidator."""
    pass

class AlgorithmSyntaxValidator(SyntaxValidator):
    """Algorithm syntax validator class."""

    def __init__(self):
        super(AlgorithmSyntaxValidator, self).__init__()
        self.addRule(CombBxOffset)
        self.addRule(DistNrObjects)
        self.addRule(DistDeltaEtaRange)

class CombBxOffset(SyntaxRule):
    """Validates that all objects of a combination function use the same BX offset."""

    def validate(self, expression):
        pass

class DistNrObjects(SyntaxRule):
    """Limit number of objects for distance function."""

    def validate(self, expression):
        tmGrammar.Algorithm_Logic.clear()
        if not tmGrammar.Algorithm_parser(expression):
            raise AlgorithmSyntaxError()
        for token in tmGrammar.Algorithm_Logic.getTokens():
            if isFunction(token):
                if token.startswith(tmGrammar.dist):
                    f = tmGrammar.Function_Item()
                    if not tmGrammar.Function_parser(token, f):
                        raise AlgorithmSyntaxError(str(f.message))
                    objects = functionObjects(token)
                    if len(objects) != 2:
                        raise AlgorithmSyntaxError("dist{{...}} function requires excactly two objects. Error near `{token}'".format(**locals()))

class DistDeltaEtaRange(SyntaxRule):
    """Validates that delta-eta cut ranges does not exceed assigned objects limits."""

    def validate(self, expression):
        tmGrammar.Algorithm_Logic.clear()
        if not tmGrammar.Algorithm_parser(expression):
            raise AlgorithmSyntaxError()
        for token in tmGrammar.Algorithm_Logic.getTokens():
            if isFunction(token):
                if token.startswith(tmGrammar.dist):
                    cuts = functionCuts(token)
                    for cut in cuts:
                        if cut.startswith(tmGrammar.DETA):
                            objects = functionObjects(token)
                            if len(objects) != 2:
                                raise AlgorithmSyntaxError("dist function requires two objects")
                            print "{"
                            for object in objects:
                                o = tmGrammar.Object_Item()
                                if not tmGrammar.Object_parser(object, o):
                                    raise AlgorithmSyntaxError("not an object")
                                print " ", o.getObjectName()
                            print "}"
