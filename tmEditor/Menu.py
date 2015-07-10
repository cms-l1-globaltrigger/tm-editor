# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Menu container, wrapping tmTable and XML bindings.

TODO: still lacking of external signals handling...

"""

import tmTable
import tmGrammar

from tmEditor import Toolbox
from tmEditor import TempFileEnvironment

import uuid
import shutil
import tempfile
import logging
import sys, os

__all__ = ['Menu', ]

FORMAT_FLOAT = '+23.16E'

class Menu(object):
    """L1-Trigger Menu container class."""

    def __init__(self, filename = None):
        self.menu = {}
        self.algorithms = []
        self.cuts = []
        self.objects = []
        self.externals = []
        self.scales = None
        self.extSignals = None
        if filename:
            self.loadXml(filename)

    def addObject(self, name, type, threshold, requirement_id = 0, comparison_operator = '.ge.', bx_offset = 0, comment = ""):
        """Provided for convenience."""
        self.objects.append(Object(
            requirement_id = requirement_id,
            name = name,
            type = type,
            threshold = threshold,
            comparison_operator = comparison_operator,
            bx_offset = bx_offset,
            comment = comment,
        ))

    def addCut(self, name, object, type, minimum, maximum, cut_id = 0, data = "", comment = ""):
        """Provided for convenience."""
        self.cuts.append(Cut(
            cut_id = cut_id,
            name = name,
            object = object,
            type = type,
            minimum = minimum,
            maximum = maximum,
            data = data,
            comment = comment,
        ))

    def addExternal(self, name, requirement_id = 0, ext_signal_id = 0, bx_offset = 0, comment = ""):
        """Provided for convenience."""
        self.externals.append(External(
            requirement_id = requirement_id,
            ext_signal_id = ext_signal_id,
            name = name,
            bx_offset = bx_offset,
            comment = comment,
        ))

    def addAlgorithm(self, index, name, expression, algorithm_id = 0, module_id = 0, module_index = 0, comment = ""):
        """Provided for convenience."""
        self.algorithms.append(Algorithm(
            algorithm_id = algorithm_id,
            index = index,
            name = name,
            expression = expression,
            module_id = module_id,
            module_index = module_index,
            comment = comment,
        ))

    def algorithmByName(self, name):
        """Returns algorithm item by its name or None if no such algorithm exists."""
        return (filter(lambda item: item.name == name, self.algorithms) or [None])[0]

    def objectByName(self, name):
        """Returns object requirement item by its name or None if no such object requirement exists."""
        return (filter(lambda item: item.name == name, self.objects) or [None])[0]

    def cutByName(self, name):
        """Returns cut item by its name or None if no such cut exists."""
        return (filter(lambda item: item.name == name, self.cuts) or [None])[0]

    def externalByName(self, name):
        """Returns external signal item by its name or None if no such external signal exists."""
        return (filter(lambda item: item.name == name, self.externals) or [None])[0]

    def loadXml(self, filename):
        """Read XML menu from file. Provided for convenience."""
        filename = os.path.abspath(filename)

        # Create virtual filesystem environment.
        with TempFileEnvironment(filename) as env:

            # Load tables from XML file.
            menu = tmTable.Menu()
            scale = tmTable.Scale()
            ext_signal = tmTable.ExtSignal()

            # Read from XML file.
            logging.debug("reading XML file from `%s'", filename)
            warnings = tmTable.xml2menu(env.filename, menu, scale, ext_signal)

            # Handle errors only after removing the temporary files.
            if warnings:
                messange = "Failed to read XML menu {filename}\n{warnings}".format(**locals())
                logging.error(messange)
                raise RuntimeError(messange)

            # Populate the containers.
            self.menu = dict(menu.menu.items())
            for algorithm in menu.algorithms:
                algorithm = Algorithm(algorithm.items())
                logging.debug("adding algorithm `%s'", algorithm)
                self.addAlgorithm(**algorithm)
            buffer = []
            for cuts in menu.cuts.values():
                for cut in cuts:
                    cut = Cut(cut.items())
                    if not cut in buffer:
                        buffer.append(cut)
            for cut in buffer:
                logging.debug("adding cut `%s'", cut)
                self.addCut(**cut)
            buffer = []
            for objs in menu.objects.values():
                for obj in objs:
                    obj = Object(obj.items())
                    if not obj in buffer:
                        buffer.append(obj)
            for obj in buffer:
                logging.debug("adding object requirements `%s'", obj)
                self.addObject(**obj)
            buffer = []
            for externals in menu.externals.values():
                for external in externals:
                    external = External(external.items())
                    if not external in buffer:
                        buffer.append(external)
            for ext in buffer:
                logging.debug("adding externals signal `%s'", ext)
                self.addExternal(**ext)
            self.scales = scale
            self.extSignals = ext_signal

    def saveXml(self, filename):
        """Provided for convenience."""
        filename = os.path.abspath(filename)

        # Create virtual filesystem environment.
        with TempFileEnvironment(filename) as env:

            # Regenerate menu UUID.
            self.menu['uuid_menu'] = str(uuid.uuid4())
            # Reset firmware UUID.
            self.menu['uuid_firmware'] = '00000000-0000-0000-0000-000000000000'
            # Create a new menu instance.
            menu = tmTable.Menu()

            # Algorithms
            for key, value in self.menu.items():
                menu.menu[key] = str(value)
            for algorithm in self.algorithms:

                if not algorithm.isValid():
                    raise RuntimeError("NOT AN ALGO")

                row = algorithm.toRow()
                menu.algorithms.append(row)

                # Objects
                if algorithm['name'] not in menu.objects:
                    menu.objects[algorithm['name']] = []
                for name in algorithm.objects():

                    object_ = self.objectByName(name)
                    if not object_.isValid():
                        raise RuntimeError("NOT AN OBJREQ")

                    row = object_.toRow()
                    menu.objects[algorithm['name']] = menu.objects[algorithm['name']] + (row, )

                # Externals
                if algorithm['name'] not in menu.externals:
                    menu.externals[algorithm['name']] = []
                for name in algorithm.externals():

                    external = self.externalByName(name)
                    if not external.isValid():
                        raise RuntimeError("NOT AN EXTERNAL")

                    row = external.toRow()
                    menu.externals[algorithm['name']] = menu.externals[algorithm['name']] + (row, )

                # Cuts
                if algorithm['name'] not in menu.cuts:
                    menu.cuts[algorithm['name']] = []
                for name in algorithm.cuts():

                    cut = self.cutByName(name)

                    if not cut.isValid():
                        raise RuntimeError("NOT AN CUT")

                    row = cut.toRow()
                    menu.cuts[algorithm['name']] = menu.cuts[algorithm['name']] + (row, )

            # Write to XML file.
            logging.debug("writing XML file to `%s'", filename)
            warnings = tmTable.menu2xml(menu, self.scales, self.extSignals, filename)

            # Handle errors only after removing the temporary files.
            if warnings:
                messange = "Failed to write XML menu {filename}\n{warnings}".format(**locals())
                logging.error(messange)
                raise RuntimeError(messange)

# ------------------------------------------------------------------------------
#  Abstract base container class.
# ------------------------------------------------------------------------------

class AbstractDict(dict):

    def isValid(self):
        raise NotImplementedError()

    def toRow(self):
        row = tmTable.Row()
        for key, value in self.items():
            row[key] = str(value)
        return row

# ------------------------------------------------------------------------------
#  Algorithm's container class.
# ------------------------------------------------------------------------------

class Algorithm(AbstractDict):
    @property
    def index(self):
        return self['index']
    @property
    def name(self):
        return self['name']
    @property
    def expression(self):
        return self['expression']

    def tokens(self):
        """Returns list of tokens of algorithm expression."""
        tmGrammar.Algorithm_Logic.clear()
        if not tmGrammar.Algorithm_parser(self.expression):
            raise NotImplementedError
        return tmGrammar.Algorithm_Logic.getTokens()

    def objects(self):
        # TODO ...come on, that's crazy insane!! >_<'''
        objects = set()
        for token in self.tokens():
            for name in tmGrammar.objectName:
                if token.startswith(name):
                    o = tmGrammar.Object_Item()
                    if not tmGrammar.Object_parser(token, o):
                        raise NotImplementedError
                    # Re-Constructing the items name.
                    comparison = o.comparison if o.comparison != ".ge." else ''
                    threshold = o.threshold
                    bx_offset = o.bx_offset if int(o.bx_offset) else ''
                    objects.add("{name}{comparison}{threshold}{bx_offset}".format(**locals()))
            for name in tmGrammar.functionName:
                if token.startswith(name):
                    o = tmGrammar.Function_Item()
                    if not tmGrammar.Function_parser(token, o):
                        raise NotImplementedError
                    for object in tmGrammar.Function_getObjects(o):
                        objects.add(object)
        return list(objects)

    def cuts(self):
        # TODO ...come on, that's crazy insane!! >_<'''
        cuts = set()
        for token in self.tokens():
            for name in tmGrammar.objectName:
                if token.startswith(name):
                    o = tmGrammar.Object_Item()
                    if not tmGrammar.Object_parser(token, o):
                        raise NotImplementedError
                    # Re-Constructing the items name.
                    for cut in o.cuts:
                        if cut:
                            cuts.add(cut)
            for name in tmGrammar.functionName:
                if token.startswith(name):
                    o = tmGrammar.Function_Item()
                    if not tmGrammar.Function_parser(token, o):
                        raise NotImplementedError
                    for cut in tmGrammar.Function_getObjectCuts(o):
                        if cut:
                            cuts.add(cut)
        return list(cuts)

    def externals(self):
        # TODO ...come on, that's crazy insane!! >_<'''
        externals = set()
        for token in self.tokens():
            pass
        return list(externals)

    def isValid(self):
        return tmTable.isAlgorithm(self.toRow())

# ------------------------------------------------------------------------------
#  Cut's container class.
# ------------------------------------------------------------------------------

class Cut(AbstractDict):
    @property
    def name(self):
        return self['name']

    def isValid(self):
        return tmTable.isCut(self.toRow())

    def toRow(self):
        row = super(Cut, self).toRow()
        row['minimum'] = format(float(row['minimum']), FORMAT_FLOAT)
        row['maximum'] = format(float(row['maximum']), FORMAT_FLOAT)
        return row

# ------------------------------------------------------------------------------
#  Object's container class.
# ------------------------------------------------------------------------------

class Object(AbstractDict):
    @property
    def name(self):
        return self['name']

    @property
    def threshold(self):
        return self['threshold']

    def isValid(self):
        return tmTable.isObjectRequirement(self.toRow())

    def toRow(self):
        row = super(Object, self).toRow()
        row['threshold'] = format(float(row['threshold']), FORMAT_FLOAT)
        return row

# ------------------------------------------------------------------------------
#  External's contianer class.
# ------------------------------------------------------------------------------

class External(AbstractDict):
    @property
    def name(self):
        return self['name']

    def isValid(self):
        return tmTable.isExternalRequirement(self.toRow())
