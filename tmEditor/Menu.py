# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

# TODO
# separate encoding/decoding
# add scales container
# add externals container
# get rid of dictionary objects

"""Menu container, wrapping tmTable and XML bindings.

"""

import tmTable
import tmGrammar

from tmEditor import Toolbox

from distutils.version import StrictVersion

import uuid
import shutil
import json
import logging
import re
import sys, os

__all__ = ['Menu', ]

GrammarVersion = StrictVersion('0.4')
"""Supported grammar version."""

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kBxOffset = 'bx_offset'
kCable = 'cable'
kChannel = 'channel'
kComment = 'comment'
kComparisonOperator = 'comparison_operator'
kData = 'data'
kDescription = 'description'
kExpression = 'expression'
kGrammarVersion = 'grammar_version'
kIndex = 'index'
kLabel = 'label'
kMaximum = 'maximum'
kMinimum = 'minimum'
kModuleId = 'module_id'
kModuleIndex = 'module_index'
kNBits = 'n_bits'
kNModules = 'n_modules'
kName = 'name'
kObject = 'object'
kStep = 'step'
kSystem = 'system'
kThreshold = 'threshold'
kType = 'type'
kUUIDFirmware = 'uuid_firmware'
kUUIDMenu = 'uuid_menu'

DEFAULT_UUID = '00000000-0000-0000-0000-000000000000'
"""Empty UUID"""

FORMAT_FLOAT = '+23.16E'
"""Floating point string format."""

ObjectTypes = (
    # Muon objects
    tmGrammar.MU,
    # Calorimeter objects
    tmGrammar.EG,
    tmGrammar.JET,
    tmGrammar.TAU,
    # Energy sums
    tmGrammar.ETT,   # ETT
    tmGrammar.ETTEM, # ETT EM
    tmGrammar.HTT,
    tmGrammar.ETM,   # ETM
    tmGrammar.ETMHF, # ETM HF
    tmGrammar.HTM,
    # Externals
    tmGrammar.EXT,
    # MinBias
    tmGrammar.MBT0HFP, # Minimum Bias Threshold 0 HF+
    tmGrammar.MBT1HFP, # Minimum Bias Threshold 1 HF+
    tmGrammar.MBT0HFM, # Minimum Bias Threshold 0 HF-
    tmGrammar.MBT1HFM, # Minimum Bias Threshold 1 HF-
    # Tower count
    tmGrammar.TOWERCOUNT,
)
"""List of supported object types (ordered)."""

CutTypes = (
    tmGrammar.ETA,
    tmGrammar.PHI,
    tmGrammar.QLTY,
    tmGrammar.ISO,
    tmGrammar.CHG,
    tmGrammar.CHGCOR,
    tmGrammar.DETA,
    tmGrammar.DPHI,
    tmGrammar.DR,
    tmGrammar.MASS,
)
"""List of supported cut types (ordered)."""

def clean(s):
    """Strip XML string entries (can contain NULL characters)."""
    return s.replace('\x00', '').strip()

def getObjectType(name):
    """Mapping object type enumeration to actual object names."""
    # WORKAROUND TODO
    for type_ in ObjectTypes:
        if name.startswith(type_):
            return type_
    message = "invalid object type `{0}`".format(type_)
    raise RuntimeError(message)

class Menu(object):
    """L1-Trigger Menu container class. Provides methods to read and write XML
    menu files and adding and removing contents.
    """

    def __init__(self, filename = None):
        self.menu = {}
        self.algorithms = []
        self.cuts = []
        self.objects = []
        self.externals = []
        self.scales = None
        self.extSignals = None
        if filename:
            self.readXml(filename)

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
        objectType = getObjectType(object.name)
        return (filter(lambda item: item[kObject]==objectType and item[kType]==scaleType, self.scales.scales) or [None])[0]

    def scaleBins(self, object, scaleType):
        """Returns bins for *object* by *scaleType*."""
        objectType = getObjectType(object.name)
        key = '{objectType}-{scaleType}'.format(**locals())
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

    def readXml(self, filename):
        """Read XML menu from *filename*. Provided for convenience."""
        filename = os.path.abspath(filename)

        # Check file accessible
        if not os.path.isfile(filename):
            message = "No such file `{0}'".format(filename)
            logging.error(message)
            raise RuntimeError(message)

        # Load tables from XML file.
        menu = tmTable.Menu()
        scale = tmTable.Scale()
        ext_signal = tmTable.ExtSignal()

        # Read from XML file.
        logging.debug("reading XML file from `%s'", filename)
        warnings = tmTable.xml2menu(filename, menu, scale, ext_signal)

        if warnings:
            message = "Failed to read XML menu {0}\n{1}".format(filename, warnings)
            logging.error(message)
            raise RuntimeError(message)

        # Verify grammar version.
        if kGrammarVersion not in menu.menu.keys():
            message = "Missing grammar version, corrupted file"
            logging.error(message)
            raise RuntimeError(message)
        grammarVersion = clean(menu.menu[kGrammarVersion])
        if not grammarVersion:
            message = "Missing grammar version, corrupted file"
            logging.error(message)
            raise RuntimeError(message)
        try:
            grammarVersion = StrictVersion(grammarVersion)
        except ValueError:
            message = "Invalid grammar version `{0}`, corrupted file".format(grammarVersion)
            logging.error(message)
            raise RuntimeError(message)
        if grammarVersion > GrammarVersion:
            message = "Unsupported grammar version {0} (requires <= {1})".format(grammarVersion, GrammarVersion)
            logging.error(message)
            raise RuntimeError(message)

        # Populate the containers.
        self.menu = dict([(k, clean(v)) for k, v in menu.menu.items()])
        self.menu[kNModules] = '0' # Reset module distribution

        # Show information about the menu.
        for k, v in self.menu.iteritems():
            logging.debug("%s: %s", k, v)

        # Add algorithms
        for table in menu.algorithms:
            index = int(table[kIndex])
            name = table[kName]
            expression = table[kExpression]
            comment = table[kComment] if kComment in table else ""
            algorithm = Algorithm(index, name, expression, comment)
            logging.debug("adding algorithm `%s'", algorithm)
            self.addAlgorithm(algorithm)
        # Add cuts
        for cuts in menu.cuts.values():
            for table in cuts:
                name = table[kName]
                object = table[kObject]
                type = table[kType]
                minimum = float(table[kMinimum])
                maximum = float(table[kMaximum])
                data = table[kData]
                comment = table[kComment] if kComment in table else ""
                # TODO
                if object == tmGrammar.comb and type == tmGrammar.CHGCOR:
                    if data.strip() == "0":
                        data = "ls"
                    if data.strip() == "1":
                        data = "os"
                cut = Cut(name, object, type, minimum, maximum, data, comment)
                if cut.type not in CutTypes:
                    message = "Unsupported cut type {0} (grammar version <= {1})".format(cut.type, GrammarVersion)
                    logging.error(message)
                    raise RuntimeError(message)
                if not self.cutByName(cut.name):
                    logging.debug("adding cut `%s'", cut)
                    self.addCut(cut)
        # Add objects
        for objs in menu.objects.values():
            for table in objs:
                name = table[kName]
                type = table[kType]
                threshold = table[kThreshold]
                comparison_operator = table[kComparisonOperator]
                bx_offset = table[kBxOffset]
                comment = table[kComment] if kComment in table else ""
                obj = Object(name, type, threshold, comparison_operator, bx_offset, comment)
                if obj.type not in ObjectTypes:
                    message = "Unsupported object type {0} (grammar version <= {1})".format(obj.type, GrammarVersion)
                    logging.error(message)
                    raise RuntimeError(message)
                if obj.type not in [scaleSet[kObject] for scaleSet in scale.scales]:
                    algorithm = self.algorithmsByObject(obj)[0]
                    message = "Object type `{0}' assigned to algorithm `{1} {2}' is missing in scales set `{3}'".format(obj.type, algorithm.index, algorithm.name, scale.scaleSet[kName])
                    logging.error(message)
                    raise RuntimeError(message)
                if not obj in self.objects:
                    logging.debug("adding object requirements `%s'", obj)
                    self.addObject(obj)
        # Add external signals
        ext_signal_names = [item['name'] for item in ext_signal.extSignals]
        ext_signal_set_name = ext_signal.extSignalSet['name']
        for externals in menu.externals.values():
            for table in externals:
                name = table[kName]
                bx_offset = table[kBxOffset]
                comment = table[kComment] if kComment in table else ""
                external = External(name, bx_offset, comment)
                # Verify that all external signals are part of the external signal set.
                if external.signal_name not in ext_signal_names:
                    algorithm = self.algorithmsByExternal(external)[0]
                    message = "External signal `{0}' assigned to algorithm `{1} {2}' is missing in external signal set `{3}'".format(external.basename, algorithm.index, algorithm.name, ext_signal_set_name)
                    logging.error(message)
                    raise RuntimeError(message)
                if external not in self.externals:
                    logging.debug("adding external signal `%s'", external)
                    self.addExternal(external)
        self.scales = scale
        self.extSignals = ext_signal

    def writeXml(self, filename):
        """Writes menu to *filename*."""
        filename = os.path.abspath(filename)

        logging.debug("preparing menu to write to `%s`", filename)

        # WORKAROUND (menu2xml() will not fail on write error...)
        if os.path.isfile(filename):
            if not os.access(filename, os.W_OK):
                message = "permission denied `{0}`".format(filename)
                logging.error(message)
                raise RuntimeError(message)
        else:
            if not os.access(os.path.dirname(filename), os.W_OK):
                message = "permission denied `{0}`".format(filename)
                logging.error(message)
                raise RuntimeError(message)

        pwd = os.getcwd()
        os.chdir(Toolbox.getXsdDir())

        try:
            self.menu[kUUIDMenu] = str(uuid.uuid4())
            logging.debug("regenerate %s=%s", kUUIDMenu, self.menu[kUUIDMenu])

            self.menu[kUUIDFirmware] = DEFAULT_UUID
            logging.debug("reset %s=%s", kUUIDFirmware, self.menu[kUUIDFirmware])

            self.menu[kGrammarVersion] = str(GrammarVersion) # updated grammar version

            # Create a new menu instance.
            menu = tmTable.Menu()

            # Algorithms
            for key, value in self.menu.items():
                menu.menu[key] = str(value)
            logging.debug("menu information : %s", dict(menu.menu))

            # Reset module distribution
            menu.menu[kNModules] = '0'
            logging.debug("reset %s=%s", kNModules, menu.menu[kNModules])

            for algorithm in self.algorithms:

                if not algorithm.isValid():
                    os.chdir(pwd)
                    message = "invalid algorithm ({algorithm.index}): {algorithm.name}".format(algorithm=algorithm)
                    logging.error(message)
                    raise RuntimeError(message)

                row = algorithm.toRow()
                logging.debug("appending algorithm %s", dict(row))
                menu.algorithms.append(row)

                # Objects
                if algorithm.name not in menu.objects.keys():
                    menu.objects[algorithm.name] = []
                for name in algorithm.objects():

                    object_ = self.objectByName(name)
                    if not object_ or not object_.isValid():
                        message = "invalid object requirement: {0}".format(name)
                        logging.error(message)
                        raise RuntimeError(message)

                    row = object_.toRow()
                    logging.debug("appending object requirement %s", dict(row))
                    menu.objects[algorithm.name] = menu.objects[algorithm.name] + (row, )

                # Externals
                if algorithm.name not in menu.externals.keys():
                    menu.externals[algorithm.name] = []
                for name in algorithm.externals():

                    external = self.externalByName(name)
                    if not external or not external.isValid():
                        message = "invalid external signal: {0}".format(name)
                        logging.error(message)
                        raise RuntimeError(message)

                    row = external.toRow()
                    logging.debug("appending external signal %s", dict(row))
                    menu.externals[algorithm.name] = menu.externals[algorithm.name] + (row, )

                # Cuts
                if algorithm.name not in menu.cuts.keys():
                    menu.cuts[algorithm.name] = []
                for name in algorithm.cuts():

                    cut = self.cutByName(name)
                    if not cut or not cut.isValid():
                        message = "Invalid cut: {0}".format(name)
                        logging.error(message)
                        raise RuntimeError(message)
                    row = cut.toRow()
                    logging.debug("appending cut %s", dict(row))
                    menu.cuts[algorithm.name] = menu.cuts[algorithm.name] + (row, )

            # Write to XML file.
            logging.debug("writing XML file to `%s'", filename)
            tmTable.menu2xml(menu, self.scales, self.extSignals, filename)
            # WORKAROUND (check if file was written)
            if not os.path.isfile(filename):
                message = "failed to write to file `{0}'".format(filename)
                logging.error(message)
                raise RuntimeError(message)

        except:
            os.chdir(pwd)
            raise

# ------------------------------------------------------------------------------
#  Abstract base container class.
# ------------------------------------------------------------------------------

class AbstractTable(object):

    def isValid(self):
        """To be implemented in derived class."""
        raise NotImplementedError()

    def toRow(self):
        """To be implemented in derived class."""
        raise NotImplementedError()

# ------------------------------------------------------------------------------
#  Algorithm's container class.
# ------------------------------------------------------------------------------

class Algorithm(AbstractTable):

    def __init__(self, index, name, expression, comment=None):
        self.index = index
        self.name = name
        self.expression = expression
        self.comment = comment or ""

    def __eq__(self, item):
        """Distinquish algorithms."""
        return (self.index, self.name, self.expression) == (item.index, item.name, item.expression)

    def __lt__(self, item):
        """Custom sorting by index, name and expression."""
        return (self.index, self.name, self.expression) < (item.index, item.name, item.expression)

    def isValid(self):
        return tmTable.isAlgorithm(self.toRow())

    def toRow(self):
        """Returns a table row object."""
        row = tmTable.Row()
        row[kIndex] = str(self.index)
        row[kModuleId] = "0"
        row[kModuleIndex] = row[kIndex]
        row[kName] = self.name
        row[kExpression] = self.expression
        row[kComment] = self.comment
        return row

    def tokens(self):
        """Returns list of RPN tokens of algorithm expression. Note that paranthesis is not included in RPN."""
        tmGrammar.Algorithm_Logic.clear()
        if not tmGrammar.Algorithm_parser(self.expression):
            raise ValueError("Failed to parse algorithm expression")
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
                for object in functionObjects(token):
                    if not object.name in objects:
                        objects.add(object.name)
        return list(objects)

    def externals(self):
        """Returns list of external names used in the algorithm's expression."""
        externals = set()
        for token in self.tokens():
            if isExternal(token):
                external = toExternal(token)
                if not external.name in externals:
                    externals.add(external.name)
        return list(externals)

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

# ------------------------------------------------------------------------------
#  Cut's container class.
# ------------------------------------------------------------------------------

class Cut(AbstractTable):

    def __init__(self, name, object, type, minimum=None, maximum=None, data=None, comment=None):
        self.name = name
        self.object = object
        self.type = type
        self.minimum = minimum or 0. if not data else ""
        self.maximum = maximum or 0. if not data else ""
        self.data = data or ""
        self.comment = comment or ""

    @property
    def typename(self):
        return '-'.join([self.object, self.type])

    @property
    def suffix(self):
        return self.name[len(self.typename) + 1:] # TODO

    def __eq__(self, item):
        """Distinquish cuts by it's uinque name."""
        return self.name == item.name
        #return (self.name, self.object, self.type, self.minimum, self.maximum, self.data) == (item.name, item.object, item.type, item.minimum, item.maximum, item.data)

    def __lt__(self, item):
        """Custom sorting by type and object and suffix name."""
        return (self.type, self.object, self.suffix) < (item.type, item.object, item.suffix)

    def isValid(self):
        return tmTable.isCut(self.toRow())

    def scale(self, scale):
        if self.typename in scale.bins.keys():
            return scale.bins[self.typename]

    def toRow(self):
        row = tmTable.Row()
        row[kName] = self.name
        row[kObject] = self.object
        row[kType] = self.type
        if self.data:
            row[kMinimum] = format(0., FORMAT_FLOAT)
            row[kMaximum] = format(0., FORMAT_FLOAT)
            row[kData] = self.data
        else:
            row[kMinimum] = format(float(self.minimum), FORMAT_FLOAT)
            row[kMaximum] = format(float(self.maximum), FORMAT_FLOAT)
            row[kData] = ""
        row[kComment] = self.comment
        return row

# ------------------------------------------------------------------------------
#  Object's container class.
# ------------------------------------------------------------------------------

class Object(AbstractTable):

    def __init__(self, name, type, threshold, comparison_operator=tmGrammar.GE, bx_offset=None, comment=None):
        self.name = name
        self.type = type
        self.threshold = threshold
        self.comparison_operator = comparison_operator
        self.bx_offset = bx_offset or 0
        self.comment = comment or ""

    def signature(self):
        return "{self.name}{self.threshold}{self.bx_offset}".format(**locals())

    def __eq__(self, item):
        """Distinquish objects."""
        return \
            (self.type, self.comparison_operator, thresholdFloat(self.threshold), self.bx_offset) == \
            (item.type, item.comparison_operator, thresholdFloat(item.threshold), item.bx_offset)

    def __lt__(self, item):
        """Custom sorting by type, threshold and offset."""
        return \
            (self.type, thresholdFloat(self.threshold), self.bx_offset) < \
            (item.type, thresholdFloat(item.threshold), item.bx_offset)

    def isValid(self):
        return tmTable.isObjectRequirement(self.toRow())

    def toRow(self):
        row = tmTable.Row()
        row[kName] = self.name
        row[kType] = self.type
        row[kThreshold] = self.threshold
        row[kComparisonOperator] = self.comparison_operator
        row[kBxOffset] = str(self.bx_offset)
        row[kThreshold] = format(thresholdFloat(self.threshold), FORMAT_FLOAT)
        return row

# ------------------------------------------------------------------------------
#  External's contianer class.
# ------------------------------------------------------------------------------

class External(AbstractTable):

    RegexSignalName = re.compile(r"(EXT_)([\w\d\._]+)([+-]\d+)?")

    def __init__(self, name, bx_offset=None, comment=None):
        self.name = name
        self.bx_offset = bx_offset or 0
        self.comment = comment or ""

    @property
    def basename(self):
        """Returns signal name with leading EXT_ prefix but without BX offset."""
        result = self.RegexSignalName.match(self.name)
        if result:
            return ''.join((result.group(1), result.group(2)))
        return self.name

    @property
    def signal_name(self):
        """Returns signal name without leading EXT_ prefix."""
        result = self.RegexSignalName.match(self.name)
        if result:
            return result.group(2)
        return self.name

    def __eq__(self, item):
        """Distinquish objects."""
        return self.basename == item.basename and self.bx_offset == item.bx_offset

    def __lt__(self, item):
        """Custom sorting by basename and offset."""
        return (self.basename, self.bx_offset) < (item.basename, item.bx_offset)

    def isValid(self):
        return tmTable.isExternalRequirement(self.toRow())

    def toRow(self):
        """Returns a table row object."""
        row = tmTable.Row()
        row[kName] = self.name
        row[kBxOffset] = str(self.bx_offset)
        row[kComment] = self.comment
        return row

# ------------------------------------------------------------------------------
#  Helper functions (wrapping/avoiding weird tmGrammar API).
# ------------------------------------------------------------------------------

def isOperator(token):
    """Retruns True if token is an logical operator."""
    return tmGrammar.isGate(token)

def isObject(token):
    """Retruns True if token is an object."""
    return tmGrammar.isObject(token) and not token.startswith(tmGrammar.EXT)

def isExternal(token):
    """Retruns True if token is an external signal."""
    return tmGrammar.isObject(token) and token.startswith(tmGrammar.EXT)

def isCut(token):
    """Retruns True if token is a cut."""
    return filter(lambda item: token.startswith(item), tmGrammar.cutName) != []

def isFunction(token):
    """Retruns True if token is a function."""
    return tmGrammar.isFunction(token)

def thresholdFloat(string):
    """Converts threshold string representation (eg. 2p1) to flaoting point value."""
    return float('.'.join(string.split('p')[:2]))

def toObject(token):
    """Returns an object's dict."""
    o = tmGrammar.Object_Item()
    if not tmGrammar.Object_parser(token, o):
        raise ValueError(token)
    return Object(
        name=o.getObjectName(),
        threshold=o.threshold,
        type=getObjectType(o.getObjectName()),
        comparison_operator=o.comparison,
        bx_offset=int(o.bx_offset)
    )

def toExternal(token):
    """Returns an external's dict."""
    # Test if external signal ends with bunch crossign offset.
    result = re.match('.*(\+\d+|\-\d+)$', token)
    bx_offset = result.group(1) if result else '+0'
    return External(
        name=token,
        bx_offset=int(bx_offset)
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

def tokens(self, expression):
    """Parses algorithm expression and returns list of tokens."""
    tmGrammar.Algorithm_Logic.clear()
    if not tmGrammar.Algorithm_parser(expression):
        message = "Failed to parse algorithm expression `{0}'".format(expression)
        raise AlgorithmSyntaxError(message)
    return tmGrammar.Algorithm_Logic.getTokens()
