# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Menu container.

"""

import tmGrammar

import Toolbox
from tmEditor.core.Settings import MaxAlgorithms
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError
from tmEditor.core.Algorithm import toObject, toExternal
from tmEditor.core.Algorithm import Algorithm
from tmEditor.core.Algorithm import Cut, Object, External

from distutils.version import StrictVersion

import logging
import uuid
import re
import sys, os

__all__ = ['Menu', ]

GrammarVersion = StrictVersion('0.4')
"""Supported grammar version."""

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kObject = 'object'
kType = 'type'

# ------------------------------------------------------------------------------
#  Menu container class
# ------------------------------------------------------------------------------

class Menu(object):
    """L1-Trigger Menu container class. Provides methods to read and write XML
    menu files and adding and removing contents.
    """

    def __init__(self):
        self.menu = MenuInfo()
        self.algorithms = []
        self.cuts = []
        self.objects = []
        self.externals = []
        self.scales = None
        self.extSignals = None

    def addObject(self, object):
        """Creates a new object by specifing its paramters and adds it to the menu. Provided for convenience."""
        self.objects.append(object)

    def addCut(self, cut):
        """Creates a new cut by specifing its paramters and adds it to the menu. Provided for convenience."""
        self.cuts.append(cut)

    def addExternal(self, external):
        """Creates a new external signal by specifing its paramters and adds it to the menu. Provided for convenience."""
        self.externals.append(external)

    def addAlgorithm(self, algorithm):
        """Creates a new algorithm by specifing its paramters and adds it to the menu. Provided for convenience.
        **Note:** related objects must be added separately to the menu.
        """
        self.algorithms.append(algorithm)

    def extendReferenced(self, algorithm):
        """Adds missing objects and external signals referenced by the
        *algorithm* to the menu.
        """
        # Add new objects to list.
        for item in algorithm.objects():
            if not self.objectByName(item):
                self.objects.append(toObject(item))
        # Add new external to list.
        for item in algorithm.externals():
            if not self.externalByName(item):
                self.externals.append(toExternal(item))

    def algorithmByName(self, name):
        """Returns algorithm item by its *name* or None if no such algorithm exists."""
        return (filter(lambda item: item.name == name, self.algorithms) or [None])[0]

    def algorithmByIndex(self, index):
        """Returns algorithm item by its *index* or None if no such algorithm exists."""
        return (filter(lambda item: int(item.index) == int(index), self.algorithms) or [None])[0]

    def algorithmsByObject(self, object):
        """Returns list of algorithms containing *object*."""
        return filter(lambda algorithm: object.name in algorithm.objects(), self.algorithms)

    def algorithmsByExternal(self, external):
        """Returns list of algorithms containing *external* signal."""
        return filter(lambda algorithm: external.basename in algorithm.externals(), self.algorithms)

    def objectByName(self, name):
        """Returns object requirement item by its *name* or None if no such object requirement exists."""
        return (filter(lambda item: item.name == name, self.objects) or [None])[0]

    def cutByName(self, name):
        """Returns cut item by its *name* or None if no such cut exists."""
        return (filter(lambda item: item.name == name, self.cuts) or [None])[0]

    def externalByName(self, name):
        """Returns external signal item by its *name* or None if no such external signal exists."""
        return (filter(lambda item: item.name == name, self.externals) or [None])[0]

    def scaleMeta(self, object, scaleType):
        """Returns scale information for *object* by *scaleType*."""
        return (filter(lambda item: item[kObject]==object.type and item[kType]==scaleType, self.scales.scales) or [None])[0]

    def scaleBins(self, object, scaleType):
        """Returns bins for *object* by *scaleType*."""
        key = '{object.type}-{scaleType}'.format(**locals())
        return self.scales.bins[key] if key in self.scales.bins else None

    def orphanedObjects(self):
        """Returns list of orphaned object names not referenced by any algorithm."""
        tags = [object.name for object in self.objects]
        for algorithm in self.algorithms:
            for name in algorithm.objects():
                if name in tags:
                    tags.remove(name)
        return tags

    def orphanedExternals(self):
        """Returns list of orphaned externals names not referenced by any algorithm."""
        tags = [external.name for external in self.externals]
        for algorithm in self.algorithms:
            for name in algorithm.objects():
                if name in tags:
                    tags.remove(name)
        return tags

    def orphanedCuts(self):
        """Returns list of orphaned cut names not referenced by any algorithm."""
        tags = [cut.name for cut in self.cuts]
        for algorithm in self.algorithms:
            for name in algorithm.cuts():
                if name in tags:
                    tags.remove(name)
        return tags

    def validate(self):
        """Consistecy check, raises exception in fail."""
        self.menu.validate()
        count = len(self.algorithms)
        if count > MaxAlgorithms:
            maximum = MaxAlgorithms
            message = "exceeding maximum number of supported algorithms: {count} (maximum {maximum})".format(**locals())
            logging.error(message)
            raise ValueError(message)
        # Temporary consistency checks
        validate = AlgorithmSyntaxValidator(self).validate
        for algorithm in self.algorithms:
            try:
                validate(algorithm.expression)
            except AlgorithmSyntaxError, e:
                message = "invalid algorithm expression: `{algorithm.expression}' in {algorithm.index} : {algorithm.name}".format(**locals())
                logging.error(message)
                raise

# ------------------------------------------------------------------------------
#  Menu information container class.
# ------------------------------------------------------------------------------

class MenuInfo(object):

    RegExMenuName = re.compile(r'^(L1Menu_)([a-zA-Z0-9_]*)$')

    def __init__(self, name=None, comment=None):
        self.name = name or ""
        self.comment = comment or ""
        self.uuid_menu = ""
        self.grammar_version = ""

    def regenerate(self):
        """Regenerate menu UUID and update grammar version."""
        self.uuid_menu = str(uuid.uuid4())
        self.grammar_version = str(GrammarVersion)

    def validate(self):
        """Run consistency checks."""
        if not self.RegExMenuName.match(self.name):
            message = "invalid menu name: `{self.name}' (must start with `L1Menu_' followed only by characters, numbers or underscores)".format(**locals())
            logging.error(message)
            raise ValueError(message)