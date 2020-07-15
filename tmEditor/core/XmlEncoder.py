"""XML encoder."""

import functools
import logging
import os

import tmTable

from tmEditor.core import toolbox

from .toolbox import safe_str
from .TableHelper import TableHelper
from .Queue import Queue
from .AlgorithmFormatter import AlgorithmFormatter

# -----------------------------------------------------------------------------
#  Keys
# -----------------------------------------------------------------------------

kAncestorId = 'ancestor_id'
kBxOffset = 'bx_offset'
kCable = 'cable'
kChannel = 'channel'
kComment = 'comment'
kComparisonOperator = 'comparison_operator'
kData = 'data'
kDescription = 'description'
kExpression = 'expression'
kGlobalTag = 'global_tag'
kGrammarVersion = 'grammar_version'
kIndex = 'index'
kIsObsolete = 'is_obsolete'
kIsValid = 'is_valid'
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

FORMAT_INDEX = 'd'
"""Algorithm index format."""

FORMAT_BX_OFFSET = '+d'
"""BX offset format, signed decimal."""


# -----------------------------------------------------------------------------
#  Decorators
# -----------------------------------------------------------------------------

def chdir(directory):
    """Execute function inside a different directory."""
    def decorate(func):
        @functools.wraps(func)
        def chdir_(*args, **kwargs):
            cwd = os.getcwd()
            logging.debug("changing to directory '%s'", directory)
            os.chdir(directory)
            try:
                result = func(*args, **kwargs)
            except:
                # Make sure to restore directory before raising an exception!
                logging.debug("returning back to directory '%s'", directory)
                os.chdir(cwd)
                raise
            logging.debug("returning back to directory '%s'", cwd)
            os.chdir(cwd)
            return result
        return chdir_
    return decorate

# -----------------------------------------------------------------------------
#  Encoder classes
# -----------------------------------------------------------------------------

class XmlEncoderError(Exception):
    """Exeption for XML encoder errors."""
    def __init__(self, message):
        super().__init__(message)

class XmlEncoderQueue(Queue):

    def __init__(self, menu, filename):
        super().__init__()
        self.menu = menu
        self.filename = os.path.abspath(filename)
        self.add_callback(self.run_prepare, "preparing writing to file")
        self.add_callback(self.run_process_info, "preparing menu info")
        self.add_callback(self.run_process_algorithms, "preparing algorithms")
        self.add_callback(self.run_process_objects, "preparing objects")
        self.add_callback(self.run_process_externals, "preparing external signals")
        self.add_callback(self.run_process_cuts, "preparing cuts")
        self.add_callback(self.run_dump_xml, "writing XML file")
        self.add_callback(self.run_verify_dump, "verifying written file")

    def run_prepare(self):
        """Write XML menu to *filename*. This regenerates the UUID."""
        logging.debug("preparing menu to write to `%s`", self.filename)

        # WORKAROUND (menu2xml() will not fail on permission denied)
        """Test if target filename is writeable by the user."""
        target = self.filename
        if not os.path.isfile(target):
            target = os.path.dirname(target)
        if not os.access(target, os.W_OK):
            message = "permission denied `{0}`".format(self.filename)
            logging.error(message)
            raise XmlEncoderError(message)

        # Setup tables
        self.tables = TableHelper()
        self.tables.scale = self.menu.scales
        self.tables.extSignal = self.menu.extSignals

    @chdir(toolbox.getXsdDir())
    def run_process_info(self):
        # Create a new menu instance.
        self.tables.menu = tmTable.Menu()

        # Regenerate UUID and version
        self.menu.menu.regenerate()
        logging.debug("regenerated menu UUID to: %s", self.menu.menu.uuid_menu)
        logging.debug("updated grammar version to: %s", self.menu.menu.grammar_version)

        # Menu inforamtion
        self.tables.menu.menu[kName] = safe_str(self.menu.menu.name, "menu name")
        self.tables.menu.menu[kComment] = safe_str(self.menu.menu.comment, "comment")
        self.tables.menu.menu[kUUIDMenu] = self.menu.menu.uuid_menu
        self.tables.menu.menu[kUUIDFirmware] = DEFAULT_UUID
        self.tables.menu.menu[kGrammarVersion] = self.menu.menu.grammar_version
        self.tables.menu.menu[kNModules] = "0"
        self.tables.menu.menu[kIsValid] = "1"
        self.tables.menu.menu[kIsObsolete] = "0"
        self.tables.menu.menu[kAncestorId] = "0"
        self.tables.menu.menu[kGlobalTag] = ""

        logging.debug("menu information: %s", dict(self.tables.menu.menu))

    @chdir(toolbox.getXsdDir())
    def run_process_algorithms(self):
        for algorithm in self.menu.algorithms:
            # Create algorithm row
            row = tmTable.Row()
            row[kIndex] = format(algorithm.index, FORMAT_INDEX)
            row[kModuleId] = "0"
            row[kModuleIndex] = format(algorithm.index, FORMAT_INDEX)
            row[kName] = safe_str(algorithm.name, "algorithm name")
            row[kExpression] = AlgorithmFormatter.compress(algorithm.expression)
            row[kComment] = algorithm.comment
            # Validate algorithm row
            if not tmTable.isAlgorithm(row):
                message = "invalid algorithm ({algorithm.index}): {algorithm.name}".format(algorithm=algorithm)
                logging.error(message)
                raise XmlEncoderError(message)
            # Append algorithm row
            logging.debug("appending algorithm: %s", dict(row))
            self.tables.menu.algorithms.append(row)

    @chdir(toolbox.getXsdDir())
    def run_process_objects(self):
        for algorithm in self.menu.algorithms:
            # Objects
            if algorithm.name not in self.tables.menu.objects.keys():
                self.tables.menu.objects[algorithm.name] = []
            for name in algorithm.objects():
                object_ = self.menu.objectByName(name)
                if not object_:
                    message = "missing object requirement: {0}".format(name)
                    logging.error(message)
                    raise XmlEncoderError(message)
                # Create object row
                row = tmTable.Row()
                row[kName] = safe_str(object_.name, "object name")
                row[kType] = object_.type
                row[kThreshold] = format(object_.decodeThreshold(), FORMAT_FLOAT)
                row[kComparisonOperator] = object_.comparison_operator
                row[kBxOffset] = format(object_.bx_offset, FORMAT_BX_OFFSET)
                # Validate object row
                if not tmTable.isObjectRequirement(row):
                    message = "invalid object requirement: {0}".format(name)
                    logging.error(message)
                    raise XmlEncoderError(message)
                # Append object trow
                logging.debug("appending object requirement: %s", dict(row))
                self.tables.menu.objects[algorithm.name] = self.tables.menu.objects[algorithm.name] + (row, )

    @chdir(toolbox.getXsdDir())
    def run_process_externals(self):
        for algorithm in self.menu.algorithms:
            # Externals
            if algorithm.name not in self.tables.menu.externals.keys():
                self.tables.menu.externals[algorithm.name] = []
            for name in algorithm.externals():
                external = self.menu.externalByName(name)
                if not external:
                    message = "missing external signal: {0}".format(name)
                    logging.error(message)
                    raise XmlEncoderError(message)
                # Create external row
                row = tmTable.Row()
                row[kName] = safe_str(external.name, "external_name")
                row[kBxOffset] = format(external.bx_offset, FORMAT_BX_OFFSET)
                # Validate external row
                if not tmTable.isExternalRequirement(row):
                    message = "invalid external signal: {0}".format(name)
                    logging.error(message)
                    raise XmlEncoderError(message)
                # Append external row
                logging.debug("appending external signal: %s", dict(row))
                self.tables.menu.externals[algorithm.name] = self.tables.menu.externals[algorithm.name] + (row, )

    @chdir(toolbox.getXsdDir())
    def run_process_cuts(self):
        for algorithm in self.menu.algorithms:
            # Cuts
            if algorithm.name not in self.tables.menu.cuts.keys():
                self.tables.menu.cuts[algorithm.name] = []
            for name in algorithm.cuts():
                logging.debug("processing cut: %s", name)
                cut = self.menu.cutByName(name)
                if not cut:
                    message = "missing cut: {0}".format(name)
                    logging.error(message)
                    raise XmlEncoderError(message)
                # Create cut row
                row = tmTable.Row()
                row[kName] = safe_str(cut.name, "cut name")
                row[kObject] = cut.object
                row[kType] = cut.type
                if cut.data:
                    row[kMinimum] = format(0., FORMAT_FLOAT)
                    row[kMaximum] = format(0., FORMAT_FLOAT)
                    row[kData] = cut.data
                else:
                    row[kMinimum] = format(float(cut.minimum), FORMAT_FLOAT)
                    row[kMaximum] = format(float(cut.maximum), FORMAT_FLOAT)
                    row[kData] = ""
                row[kComment] = cut.comment
                #Validate cut row
                if not tmTable.isCut(row):
                    message = "invalid cut: {0}".format(name)
                    logging.error(message)
                    raise XmlEncoderError(message)
                # Append cut row
                logging.debug("appending cut: %s", dict(row))
                self.tables.menu.cuts[algorithm.name] = self.tables.menu.cuts[algorithm.name] + (row, )

    @chdir(toolbox.getXsdDir())
    def run_dump_xml(self):
        # Write to XML file.
        logging.debug("writing XML file to `%s'", self.filename)
        self.tables.dump(self.filename)

    def run_verify_dump(self):
        # WORKAROUND (check if file was written)
        if not os.path.isfile(self.filename):
            message = "failed to write to file `{0}'".format(self.filename)
            logging.error(message)
            raise XmlEncoderError(message)

def dump(menu, filename):
    queue = XmlEncoderQueue(menu, filename)
    queue.exec_()
