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

OBJECT_CODES = {
    tmGrammar.Muon: tmGrammar.MU,
    tmGrammar.Egamma: tmGrammar.EG,
    tmGrammar.Jet: tmGrammar.JET,
    tmGrammar.Tau: tmGrammar.TAU,
    tmGrammar.External: tmGrammar.EXT,
}

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
        """To be implemented in derived class."""
        raise NotImplementedError()

    def toRow(self):
        """Returns a table row object."""
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

    @property
    def module_index(self):
        return self['module_index']

    @property
    def module_id(self):
        return self['module_id']

    def isValid(self):
        return tmTable.isAlgorithm(self.toRow())

    def tokens(self):
        """Returns list of tokens of algorithm expression. Paranthesis is not included."""
        tmGrammar.Algorithm_Logic.clear()
        if not tmGrammar.Algorithm_parser(self.expression):
            raise ValueError()
        return list(tmGrammar.Algorithm_Logic.getTokens())

    def objects(self):
        """Returns list of object names used in the algorithm's expression."""
        objects = set()
        for token in self.tokens():
            if isObject(token):
                object = toObject(token) # Cast to object required to fetch complete name.
                if not object.name in objects:
                    objects.add(object.name)
            if isFunction(token):
                for object in functionObjects(token): # Cast to objects required to fetch complete name.
                    if not object.name in objects:
                        objects.add(object.name)
        return list(objects)

    def cuts(self):
        """Returns list of cut names used in the algorithm's expression."""
        cuts = set()
        for token in self.tokens():
            if isObject(token):
                for cut in objectCuts(token):
                    if not cut in cuts:
                        cuts.add(cut)
            if isFunction(token):
                for cut in functionCuts(token):
                    if not cut in cuts:
                        cuts.add(cut)
                for cut in functionObjectsCuts(token):
                    if not cut in cuts:
                        cuts.add(cut)
        return list(cuts)

    def externals(self):
        externals = set()
        for token in self.tokens():
            if isOperator(token):
                continue
            if isObject(token):
                continue
            if isFunction(token):
                continue
            # Must be an external I would guess...
            externals.add(token)
        return list(externals)

# ------------------------------------------------------------------------------
#  Cut's container class.
# ------------------------------------------------------------------------------

class Cut(AbstractDict):

    @property
    def name(self):
        return self['name']

    @name.setter
    def name(self, name):
        self['name'] = str(name)

    @property
    def minimum(self):
        return self['minimum']

    @property
    def maximum(self):
        return self['maximum']

    @property
    def data(self):
        return self['data']

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
        row['threshold'] = format(float(row['threshold'].replace('p', '.')), FORMAT_FLOAT)
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

def isOperator(token):
    """Retruns True if token is an logical operator."""
    return token in tmGrammar.gateName

def isObject(token):
    """Retruns True if token is an object."""
    return filter(lambda item: token.startswith(item), tmGrammar.objectName) != []

def isCut(token):
    """Retruns True if token is a cut."""
    return filter(lambda item: token.startswith(item), tmGrammar.cutName) != []

def isFunction(token):
    """Retruns True if token is a function."""
    return filter(lambda item: token.startswith(item), tmGrammar.functionName) != []

def toObject(token):
    """Returns an object dict."""
    o = tmGrammar.Object_Item()
    if not tmGrammar.Object_parser(token, o):
        raise ValueError(token)
    return Object(
        name = o.getObjectName(),
        threshold = o.threshold,
        type = OBJECT_CODES[o.type],
        comparison_operator = o.comparison,
        bx_offset = o.bx_offset,
        comment = "",
    )

def functionObjects(token):
    """Returns list of object dicts assigned to a function."""
    objects = []
    f = tmGrammar.Function_Item()
    if not tmGrammar.Function_parser(token, f):
        raise ValueError(token)
    for token in tmGrammar.Function_getObjects(f):
        if isObject(token):
            objects.append(toObject(token))
    return objects

def functionCuts(token):
    """Returns list of cut names assigned to a function."""
    cuts = []
    f = tmGrammar.Function_Item()
    if not tmGrammar.Function_parser(token, f):
        raise ValueError(token)
    for name in tmGrammar.Function_getCuts(f):
        cuts.append(name)
        print name
    return cuts

def functionObjectsCuts(token):
    """Returns list of cut names assigned to function objects."""
    cuts = []
    f = tmGrammar.Function_Item()
    if not tmGrammar.Function_parser(token, f):
        raise ValueError(token)
    for token in tmGrammar.Function_getObjects(f):
        o = tmGrammar.Object_Item()
        if not tmGrammar.Object_parser(token, o):
            raise ValueError(token)
        for name in o.cuts:
            cuts.append(name)
            print name
    return cuts

def objectCuts(token):
    """Returns list of cut names assigned to an object."""
    cuts = []
    o = tmGrammar.Object_Item()
    if not tmGrammar.Object_parser(token, o):
        raise ValueError(token)
    return list(o.cuts)
