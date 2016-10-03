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

>>> validator = AlgorithmSyntaxValidator(menu)
>>> validator.validate(expression)

"""

import tmGrammar

from tmEditor.Menu import (
    isOperator,
    isObject,
    isExternal,
    isCut,
    isFunction,
    toObject,
    thresholdFloat,
    functionObjects,
    functionCuts,
    functionObjectsCuts,
    objectCuts,
)

import logging

__all__ = ['AlgorithmSyntaxValidator', 'AlgorithmSyntaxError']

# -----------------------------------------------------------------------------
#  Base classes
# -----------------------------------------------------------------------------

class SyntaxValidator(object):
    """Base class to be inherited by custom syntax validator classes."""

    def __init__(self, menu):
        self.menu = menu # menu handle
        self.rules = []

    def validate(self, expression):
        for rule in self.rules:
            rule.validate(expression)

    def addRule(self, cls):
        """Add a syntx rule class. Creates and tores an instance of the class."""
        self.rules.append(cls(self))

class SyntaxRule(object):
    """Base class to be inherited by custom syntax rule classes."""

    def __init__(self, validator):
        self.validator = validator

    def tokens(self, expression):
        """Parses algorithm expression and returns list of tokens."""
        # Make sure to clear static algorithm logic.
        tmGrammar.Algorithm_Logic.clear()
        # Check for empty expression
        if not expression.strip():
            raise AlgorithmSyntaxError("Empty expression")
        if not tmGrammar.Algorithm_parser(expression):
            raise AlgorithmSyntaxError("Invalid expression `{expression}'".format(**locals()))
        return tmGrammar.Algorithm_Logic.getTokens()

    def toObjectItem(self, token):
        item = tmGrammar.Object_Item()
        if not tmGrammar.Object_parser(token, item):
            raise AlgorithmSyntaxError(
                "Invalid object statement `{item.message}`".format(**locals()),
                token
            )
        return item

    def toFunctionItem(self, token):
        item = tmGrammar.Function_Item()
        if not tmGrammar.Function_parser(token, item):
            raise AlgorithmSyntaxError(
                "Invalid function statement `{item.message}`".format(**locals()),
                token
            )
        return item

    def toCutItem(self, token):
        item = tmGrammar.Cut_Item()
        if not tmGrammar.Cut_parser(token, item):
            raise AlgorithmSyntaxError(
                "Invalid cut statement `{item.message}` at object {token}".format(**locals()),
                token
            )
        return item

    def validate(self, expression):
        raise NotImplementedError()

# -----------------------------------------------------------------------------
#  Algorithm language specific classes
# -----------------------------------------------------------------------------

class AlgorithmSyntaxError(Exception):
    """Exeption for algoithm syntax errors thrown by class AlgorithmSyntaxValidator."""
    def __init__(self, message, token = None):
        super(AlgorithmSyntaxError, self).__init__(message)
        self.token = token

class AlgorithmSyntaxValidator(SyntaxValidator):
    """Algorithm syntax validator class."""

    def __init__(self, menu):
        super(AlgorithmSyntaxValidator, self).__init__(menu)
        self.addRule(BasicSyntax)
        self.addRule(CombBxOffset)
        self.addRule(ObjectThresholds)
        self.addRule(DistNrObjects)
        self.addRule(DistDeltaRange)

class BasicSyntax(SyntaxRule):
    """Validates basic algorithm syntax."""
    def validate(self, expression):
        previous = ''
        for token in self.tokens(expression):
            # Validate operators
            if isOperator(token):
                pass
            # Validate object
            elif isObject(token):
                o = self.toObjectItem(token)
                for cut in o.cuts:
                    self.toCutItem(cut)
            # Validate function
            elif isFunction(token):
                f = self.toFunctionItem(token)
                for cut in f.cuts:
                    self.toCutItem(cut)
            # Validate externals
            elif isExternal(token):
                pass
            else:
                raise AlgorithmSyntaxError("Invalid token `{token}`".format(**locals()), token)
            previous = token


class ObjectThresholds(SyntaxRule):
    """Validates object thresholds/counts."""

    def validate(self, expression):
        # TODO... better to use floating point representation and compare by string?!
        def validateThreshold(menu, token, object):
            scaleTypes = {
                tmGrammar.MU: 'ET',
                tmGrammar.EG: 'ET',
                tmGrammar.TAU: 'ET',
                tmGrammar.JET: 'ET',
                tmGrammar.ETT: 'ET',
                tmGrammar.HTT: 'ET',
                tmGrammar.ETM: 'ET',
                tmGrammar.HTM: 'ET',
                tmGrammar.ETTEM: 'ET',
                tmGrammar.ETMHF: 'ET',
                tmGrammar.MBT0HFP: 'COUNT',
                tmGrammar.MBT1HFP: 'COUNT',
                tmGrammar.MBT0HFM: 'COUNT',
                tmGrammar.MBT1HFM: 'COUNT',
                tmGrammar.TOWERCOUNT: 'COUNT',
            }
            scale = menu.scaleMeta(object, scaleTypes[object.type])
            threshold = thresholdFloat(object.threshold)
            minimum = float(scale['minimum'])
            maximum = float(scale['maximum'])
            step = float(scale['step'])
            # Check range
            if not (minimum <= threshold <= maximum):
                raise AlgorithmSyntaxError(
                    "Object threshold exceeding scale limits ({minimum:.1f}..{maximum:.1f}) near `{token}`".format(**locals()),
                    token
                )
            # Check step
            bins = menu.scaleBins(object, scaleTypes[object.type])
            if not filter(lambda bin: float(bin['minimum'])==threshold or float(bin['maximum'])==threshold, bins):
                raise AlgorithmSyntaxError(
                    "Invalid threshold `{object.threshold}` at object `{token}`".format(**locals()),
                    token
                )
        for token in self.tokens(expression):
            # Validate object
            if isObject(token):
                object = toObject(token)
                validateThreshold(self.validator.menu, token, object)
            # Validate function
            if isFunction(token):
                for object in functionObjects(token):
                    validateThreshold(self.validator.menu, token, object)

class CombBxOffset(SyntaxRule):
    """Validates that all objects of a combination function use the same BX offset."""

    def validate(self, expression):
        for token in self.tokens(expression):
            if not isFunction(token):
                continue
            if not token.startswith(tmGrammar.comb):
                continue
            f = tmGrammar.Function_Item()
            if not tmGrammar.Function_parser(token, f):
                raise AlgorithmSyntaxError(f.message)
            objects = functionObjects(token)
            for i in range(len(objects)):
                if int(objects[i].bx_offset) != int(objects[0].bx_offset):
                    raise AlgorithmSyntaxError("All object requirements of function comb{{...}} must be of same bunch crossing offset.\n" \
                                               "Invalid expression near \"{token}\"".format(**locals()), token)

class DistNrObjects(SyntaxRule):
    """Limit number of objects for distance function."""

    def validate(self, expression):
        for token in self.tokens(expression):
            if not isFunction(token):
                continue
            if not token.startswith(tmGrammar.dist):
                continue
            f = tmGrammar.Function_Item()
            if not tmGrammar.Function_parser(token, f):
                raise AlgorithmSyntaxError(str(f.message))
            objects = functionObjects(token)
            if len(objects) != 2:
                raise AlgorithmSyntaxError("Function dist{{...}} requires excactly two object requirements.\n" \
                                           "Invalid expression near \"{token}\"".format(**locals()))

class DistDeltaRange(SyntaxRule):
    """Validates that delta-eta/phi cut ranges does not exceed assigned objects limits."""

    def validate(self, expression):
        menu = self.validator.menu
        for token in self.tokens(expression):
            if not isFunction(token):
                continue
            if not token.startswith(tmGrammar.dist):
                continue
            for name in functionCuts(token):
                cut = menu.cutByName(name)
                if cut.type == tmGrammar.DETA:
                    for object in functionObjects(token):
                        scale = filter(lambda scale: scale['object']==object.type and scale['type']==tmGrammar.ETA, menu.scales.scales)[0]
                        minimum = 0
                        maximum = abs(float(scale['minimum'])) + float(scale['maximum'])
                        if not (minimum <= float(cut.minimum) <= maximum):
                            raise AlgorithmSyntaxError("Cut \"{name}\" minimum limit of {cut.minimum} exceed valid object DETA range of {minimum}".format(**locals()))
                        if not (minimum <= float(cut.maximum) <= maximum):
                            raise AlgorithmSyntaxError("Cut \"{name}\" maximum limit of {cut.maximum} exceed valid object DETA range of {maximum}".format(**locals()))
                if cut.type == tmGrammar.DPHI:
                    for object in functionObjects(token):
                        scale = filter(lambda scale: scale['object']==object.type and scale['type']==tmGrammar.PHI, menu.scales.scales)[0]
                        minimum = 0
                        maximum = float(format(float(scale['maximum']) / 2., '.3f')) # HACK
                        if not (minimum <= float(cut.minimum) <= maximum):
                            raise AlgorithmSyntaxError("Cut \"{name}\" minimum limit of {cut.minimum} exceed valid object DPHI range of {minimum}".format(**locals()))
                        if not (minimum <= float(cut.maximum) <= maximum):
                            raise AlgorithmSyntaxError("Cut \"{name}\" maximum limit of {cut.maximum} exceed valid object DPHI range of {maximum}".format(**locals()))
