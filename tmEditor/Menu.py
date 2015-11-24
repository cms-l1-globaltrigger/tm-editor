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

import uuid
import shutil
import logging
import re
import sys, os

__all__ = ['Menu', ]

DEFAULT_UUID = '00000000-0000-0000-0000-000000000000'
"""Empty UUID"""

FORMAT_FLOAT = '+23.16E'
"""Floating point string format."""

ObjectCodes = {
    tmGrammar.Muon: tmGrammar.MU,
    tmGrammar.Egamma: tmGrammar.EG,
    tmGrammar.Jet: tmGrammar.JET,
    tmGrammar.Tau: tmGrammar.TAU,
    tmGrammar.Scaler: tmGrammar.ETT,
    tmGrammar.Vector: tmGrammar.ETM,
    tmGrammar.Scaler: tmGrammar.HTT,
    tmGrammar.Vector: tmGrammar.HTM,
    tmGrammar.External: tmGrammar.EXT,
}

OperatorList = (
    tmGrammar.AND,
    tmGrammar.OR,
    tmGrammar.XOR,
    tmGrammar.NOT,
)

ObjectComparisonList = (
    tmGrammar.EQ,
    tmGrammar.NE,
    tmGrammar.GE,
    tmGrammar.GT,
    tmGrammar.LE,
    tmGrammar.LT,
)

CUT_MAPPING = {

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
            minimum = minimum if not data else '',
            maximum = maximum if not data else '',
            data = data if data else '',
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
        """Provided for convenience. Note: related objects must be added separately."""
        algorithm = Algorithm(
            algorithm_id = algorithm_id,
            index = index,
            name = name,
            expression = expression,
            module_id = module_id,
            module_index = module_index,
            comment = comment,
        )
        self.algorithms.append(algorithm)

    def updateAlgorithm(self, algorithm):
        #print "updateAlgorithm()"
        #print " global:", [o.name for o in self.objects]
        #print " pre:", algorithm.objects()
        #if algorithm not in self.algorithms: # MALICIOUS
        #    self.algorithms.append(algorithm)
        # Add new objects to list.
        for item in algorithm.objects():
            if not self.objectByName(item):
                self.objects.append(toObject(item))
        # Add new external to list.
        for item in algorithm.externals():
            if not self.externalByName(item):
                self.externals.append(toExternal(item))

    def algorithmByName(self, name):
        """Returns algorithm item by its name or None if no such algorithm exists."""
        return (filter(lambda item: item.name == name, self.algorithms) or [None])[0]

    def algorithmByIndex(self, index):
        """Returns algorithm item by its index or None if no such algorithm exists."""
        return (filter(lambda item: int(item.index) == int(index), self.algorithms) or [None])[0]

    def objectByName(self, name):
        """Returns object requirement item by its name or None if no such object requirement exists."""
        return (filter(lambda item: item.name == name, self.objects) or [None])[0]

    def cutByName(self, name):
        """Returns cut item by its name or None if no such cut exists."""
        return (filter(lambda item: item.name == name, self.cuts) or [None])[0]

    def externalByName(self, name):
        """Returns external signal item by its name or None if no such external signal exists."""
        return (filter(lambda item: item.name == name, self.externals) or [None])[0]

    def orphanedObjects(self):
        """Returns list of orphaned object names not referenced by any algorithm."""
        tags = [object.name for object in self.objects]
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

    def loadXml(self, filename):
        """Read XML menu from file. Provided for convenience."""
        filename = os.path.abspath(filename)

        # Load tables from XML file.
        menu = tmTable.Menu()
        scale = tmTable.Scale()
        ext_signal = tmTable.ExtSignal()

        # Read from XML file.
        logging.debug("reading XML file from `%s'", filename)
        warnings = tmTable.xml2menu(filename, menu, scale, ext_signal)

        if warnings:
            messange = "Failed to read XML menu {filename}\n{warnings}".format(**locals())
            logging.error(messange)
            raise RuntimeError(messange)

        # Populate the containers.
        self.menu = dict(menu.menu.items())
        # Add algorithms
        for algorithm in menu.algorithms:
            algorithm = Algorithm(algorithm.items())
            logging.debug("adding algorithm `%s'", algorithm)
            self.addAlgorithm(**algorithm)
        # Add cuts
        for cuts in menu.cuts.values():
            for cut in cuts:
                cut = Cut(cut.items())
                if not cut in self.cuts:
                    logging.debug("adding cut `%s'", cut)
                    self.addCut(**cut)
        # Add objects
        for objs in menu.objects.values():
            for obj in objs:
                obj = Object(obj.items())
                if not obj in self.objects:
                    logging.debug("adding object requirements `%s'", obj)
                    self.addObject(**obj)
        # Add externals
        for externals in menu.externals.values():
            for external in externals:
                external = External(external.items())
                if not external in self.externals:
                    logging.debug("adding external signal `%s'", external)
                    self.addExternal(**external)
        self.scales = scale
        self.extSignals = ext_signal

    def saveXml(self, filename):
        """Provided for convenience."""
        filename = os.path.abspath(filename)

        pwd = os.getcwd()
        os.chdir(Toolbox.getXsdDir())

        try:
            logging.debug("regenerating menu UUID")
            self.menu['uuid_menu'] = str(uuid.uuid4())

            logging.debug("reset firmware UUID")
            self.menu['uuid_firmware'] = DEFAULT_UUID
            # Create a new menu instance.
            menu = tmTable.Menu()

            # Algorithms
            for key, value in self.menu.items():
                menu.menu[key] = str(value)
            for algorithm in self.algorithms:

                if not algorithm.isValid():
                    os.chdir(pwd)
                    raise RuntimeError("Invalid algorithm ({algorithm.index}): {algorithm.name}".format(**locals()))

                row = algorithm.toRow()
                logging.debug("appending algorithm `%s'", algorithm.name)
                menu.algorithms.append(row)

                # Objects
                if algorithm.name not in menu.objects.keys():
                    menu.objects[algorithm.name] = []
                for name in algorithm.objects():

                    object_ = self.objectByName(name)
                    if not object_:
                        raise RuntimeError("Invalid object requirement: {name}".format(**locals()))

                    row = object_.toRow()
                    logging.debug("appending object requirement `%s'", name)
                    menu.objects[algorithm.name] = menu.objects[algorithm.name] + (row, )

                # Externals
                if algorithm.name not in menu.externals.keys():
                    menu.externals[algorithm.name] = []
                for name in algorithm.externals():

                    external = self.externalByName(name)
                    if not external:
                        raise RuntimeError("Invalid external signal: {name}".format(**locals()))

                    row = external.toRow()
                    logging.debug("appending external signal `%s'", name)
                    menu.externals[algorithm.name] = menu.externals[algorithm.name] + (row, )

                # Cuts
                if algorithm.name not in menu.cuts.keys():
                    menu.cuts[algorithm.name] = []
                for name in algorithm.cuts():

                    cut = self.cutByName(name)
                    if not cut:
                        raise RuntimeError("Invalid cut: {name}".format(**locals()))

                    row = cut.toRow()
                    logging.debug("appending cut `%s'", name)
                    menu.cuts[algorithm.name] = menu.cuts[algorithm.name] + (row, )

            # Write to XML file.
            logging.debug("writing XML file to `%s'", filename)
            tmTable.menu2xml(menu, self.scales, self.extSignals, filename)


        except:
            os.chdir(pwd)
            raise

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

    @property
    def comment(self):
        return self['comment'] if 'comment' in self.keys() else ""

    def __eq__(self, item):
        """Distinquish algorithms."""
        return (self.index, self.name, self.expression) == (item.index, item.name, item.expression)

    def __lt__(self, item):
        """Custom sorting by index, name and expression."""
        return (self.index, self.name, self.expression) < (item.index, item.name, item.expression)

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
        """Returns list of externals names used in the algorithm's expression."""
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
    def object(self):
        return self['object']

    @property
    def type(self):
        return self['type']

    @property
    def typename(self):
        return "{self.object}-{self.type}".format(**locals())

    @property
    def suffix(self):
        return self.name[len(self.typename) + 1:]

    @property
    def minimum(self):
        return self['minimum']

    @property
    def maximum(self):
        return self['maximum']

    @property
    def data(self):
        return self['data']

    def __eq__(self, item):
        """Distinquish cuts by it's uinque name."""
        return (self.name, self.object, self.type, self.minimum, self.maximum, self.data) == (item.name, item.object, item.type, item.minimum, item.maximum, item.data)

    def __lt__(self, item):
        """Custom sorting by type and object and suffix name."""
        return (self.type, self.object, self.suffix) < (item.type, item.object, item.suffix)

    def isValid(self):
        return tmTable.isCut(self.toRow())

    def scale(self, scale):
        if self.typename in scale.bins.keys():
            return scale.bins[self.typename]

    def toRow(self):
        row = super(Cut, self).toRow()
        # Workaround 1023 and 1099 ... >_<'
        row['minimum'] = format(float(row['minimum'] if not self.data else 0.), FORMAT_FLOAT)
        row['maximum'] = format(float(row['maximum'] if not self.data else 0.), FORMAT_FLOAT)
        return row

# ------------------------------------------------------------------------------
#  Object's container class.
# ------------------------------------------------------------------------------

class Object(AbstractDict):

    @property
    def name(self):
        return self['name']

    @property
    def type(self):
        return self['type']

    @property
    def comparison_operator(self):
        return self['comparison_operator']

    @property
    def threshold(self):
        return self['threshold']

    @property
    def bx_offset(self):
        return self['bx_offset']

    @property
    def comment(self):
        return self['comment'] if 'comment' in self.keys() else ''

    def signature(self):
        return "{name}{threshold}{bx_offset}".format(**self)

    def __eq__(self, item):
        """Distinquish objects."""
        return \
            self.type == item.type and \
            self.comparison_operator == item.comparison_operator and \
            self.threshold == item.threshold and \
            self.bx_offset == item.bx_offset

    def __lt__(self, item):
        """Custom sorting by type, threshold and offset."""
        return \
            (self.type, float(self.threshold.replace('p', '.')), int(self.bx_offset)) < \
            (item.type, float(item.threshold.replace('p', '.')), int(item.bx_offset))

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

    @property
    def basename(self):
        result = re.match("([\w\d\._]+)([+-]\d+)?", self.name)
        if result:
            return result.group(1)
        return self.name

    @property
    def bx_offset(self):
        return self['bx_offset']

    def __eq__(self, object):
        """Distinquish objects."""
        return self.basename == object.basename and int(self.bx_offset) == int(object.bx_offset)

    def __lt__(self, item):
        """Custom sorting by basename and offset."""
        return (self.basename, int(self.bx_offset)) < (item.basename, int(item.bx_offset))

    def isValid(self):
        return tmTable.isExternalRequirement(self.toRow())

# ------------------------------------------------------------------------------
#  Helper functions (wrapping/avoiding weird tmGrammar API).
# ------------------------------------------------------------------------------

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
    """Returns an object's dict."""
    o = tmGrammar.Object_Item()
    if not tmGrammar.Object_parser(token, o):
        raise ValueError(token)
    return Object(
        name = o.getObjectName(),
        threshold = o.threshold,
        type = ObjectCodes[o.type],
        comparison_operator = o.comparison,
        bx_offset = o.bx_offset,
        comment = "",
    )

def toExternal(token):
    """Returns an external's dict."""
    # Test if external signal ends with bunch crossign offset.
    result = re.match('.*(\+\d+|\-\d+)$', token)
    bx_offset = result.group(1) if result else '+0'
    return External(
        name = token,
        bx_offset = bx_offset,
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
    return cuts

def functionObjectsCuts(token):
    """Returns list of cut names assigned to function objects."""
    cuts = set()
    f = tmGrammar.Function_Item()
    if not tmGrammar.Function_parser(token, f):
        raise ValueError(token)
    # Note: returns string containting list of cuts.
    for names in tmGrammar.Function_getObjectCuts(f):
        if names:
            for name in names.split(','):
                cuts.add(name.strip())
    return list(cuts)

def objectCuts(token):
    """Returns list of cut names assigned to an object."""
    cuts = []
    o = tmGrammar.Object_Item()
    if not tmGrammar.Object_parser(token, o):
        raise ValueError(token)
    return list(o.cuts)
