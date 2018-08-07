# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

import tmGrammar

from tmEditor.core import Menu, toolbox
from tmEditor.core import Algorithm
from tmEditor.core import types

from tmEditor.core.toolbox import safe_str
from tmEditor.core.Queue import Queue
from tmEditor.core.TableHelper import TableHelper
from tmEditor.core.Settings import MaxAlgorithms
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError

from distutils.version import StrictVersion
from collections import namedtuple

from XmlEncoder import chdir

import logging
import sys, os
import re

# -----------------------------------------------------------------------------
#  Keys
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
#  Migration functions
# -----------------------------------------------------------------------------

MirgrationResult = namedtuple('MirgrationResult', 'subject,param,before,after')

def mirgrate_chgcor_cut(cut):
    """Migrates old CHGCOR cut data specifications:
      "0" -> "ls"
      "1" -> "os"
    """
    chgcor_mapping = {
        '0': 'ls',
        '1': 'os',
    }
    if cut.type == tmGrammar.CHGCOR:
        data = cut.data.strip()
        if data in chgcor_mapping:
            cut.data = chgcor_mapping[data]
            logging.info("migrated cut %s: '%s' => '%s'", cut.name, data, cut.data)
            return MirgrationResult(cut, 'data', data, cut.data)

def mirgrate_cut_object(cut):
    """Migrate obsolete object entries for function cuts."""
    object_ = cut.object
    if cut.type in types.FunctionCutTypes:
        object_ = cut.object
        if cut.object:
            cut.object = "" # clear
            logging.info("migrated function cut object type %s: '%s' => '%s'", cut.name, object_, cut.object)
            return MirgrationResult(cut, 'object', object_, cut.object)

def mirgrate_mass_function(algorithm):
    """Migrates old mass functions to newer mass_inv:
    "mass" -> "mass_inv"
    """
    expression = re.sub(r"\b{0}\b".format(tmGrammar.mass), tmGrammar.mass_inv, algorithm.expression)
    if algorithm.expression != expression:
        prev_expression = algorithm.expression
        algorithm.expression = expression
        logging.info("migrated function '%s' => '%s' in algorithm %s: %s", tmGrammar.mass, tmGrammar.mass_inv, algorithm.name, expression)
        return MirgrationResult(algorithm, 'expression', tmGrammar.mass, tmGrammar.mass_inv)

# -----------------------------------------------------------------------------
#  Decoder classes
# -----------------------------------------------------------------------------

class XmlDecoderError(Exception):
    """Exeption for XML decoder errors."""
    def __init__(self, message):
        super(XmlDecoderError, self).__init__(message)

class XmlDecoderQueue(Queue):

    def __init__(self, filename):
        super(XmlDecoderQueue, self).__init__()
        self.filename = os.path.abspath(filename)
        self.applied_mirgrations = []
        self.menu = None
        self.add_callback(self.run_prepare, "check access rights")
        self.add_callback(self.run_load_xml, "loading XML file")
        self.add_callback(self.run_version_check, "checking versions")
        self.add_callback(self.run_process_info, "loading menu information")
        self.add_callback(self.run_process_algorithms, "loading algorithms")
        self.add_callback(self.run_process_cuts, "loading cuts")
        self.add_callback(self.run_process_objects, "loading objects requirements")
        self.add_callback(self.run_process_externals, "loading external signals requirements")
        self.add_callback(self.run_process_scales, "loading scales")
        self.add_callback(self.run_process_ext_signals, "loading external signals")
        self.add_callback(self.run_verify_menu, "verifying menu integrity")

    def run_prepare(self):
        logging.debug("checking file access rights...")
        if not os.path.isfile(self.filename):
            message = "No such file or directory `{0}'".format(self.filename)
            logging.error(message)
            raise XmlDecoderError(message)

    @chdir(toolbox.getXsdDir())
    def run_load_xml(self):
        logging.debug("Reading XML file from `%s'", self.filename)
        self.tables = TableHelper()
        warnings = self.tables.load(self.filename)

        if warnings:
            message = "Failed to read XML menu `{0}'\n{1}".format(self.filename, warnings)
            logging.error(message)
            raise XmlDecoderError(message)

    def run_version_check(self):
        """Verify menu grammar version."""
        if kGrammarVersion not in self.tables.menu.menu.keys():
            message = "Missing grammar version, corrupted file?"
            logging.error(message)
            raise XmlDecoderError(message)
        version = self.tables.menu.menu[kGrammarVersion]
        if not version:
            message = "Missing grammar version, corrupted file?"
            logging.error(message)
            raise XmlDecoderError(message)
        try:
            version = StrictVersion(version)
        except ValueError:
            message = "Invalid grammar version `{0}`, corrupted file?".format(version)
            logging.error(message)
            raise XmlDecoderError(message)
        if version > Menu.GrammarVersion:
            message = "Unsupported grammar version {0} (requires <= {1})".format(version, Menu.GrammarVersion)
            logging.error(message)
            raise XmlDecoderError(message)

    def run_process_info(self):
        logging.debug("adding menu info...")
        self.menu = Menu.Menu()
        self.menu.menu.name = safe_str(self.tables.menu.menu[kName], "menu name")
        self.menu.menu.comment = self.tables.menu.menu[kComment] if kComment in self.tables.menu.menu else ""
        self.menu.menu.uuid_menu = self.tables.menu.menu[kUUIDMenu]
        self.menu.menu.grammar_version = self.tables.menu.menu[kGrammarVersion]

        logging.debug("loaded menu information: %s", self.menu.menu.__dict__)

    def run_process_algorithms(self):
        logging.debug("adding algorithms...")
        for row in [dict(row) for row in self.tables.menu.algorithms]:
            index = int(row[kIndex])
            name = safe_str(row[kName], "algorithm name")
            expression = row[kExpression]
            comment = row.get(kComment, "")
            algorithm = Algorithm.Algorithm(index, name, expression, comment)
            # Patch outdated expressions
            result = mirgrate_mass_function(algorithm)
            if result:
                self.applied_mirgrations.append(result)
            logging.debug("adding algorithm: %s", algorithm.__dict__)
            self.menu.addAlgorithm(algorithm)

    def run_process_cuts(self):
        logging.debug("adding cuts...")
        for cuts in self.tables.menu.cuts.values():
            for row in [dict(row) for row in cuts]:
                name = safe_str(row[kName], "cut name")
                object = row[kObject]
                type = row[kType]
                minimum = float(row[kMinimum])
                maximum = float(row[kMaximum])
                data = row[kData]
                comment = row.get(kComment, "")
                cut = Algorithm.Cut(name, object, type, minimum, maximum, data, comment)
                # Migrate old formats
                result = mirgrate_cut_object(cut)
                if result:
                    self.applied_mirgrations.append(result)
                result = mirgrate_chgcor_cut(cut)
                if result:
                    self.applied_mirgrations.append(result)
                if cut.type not in types.CutTypes:
                    message = "Unsupported cut type {0} (grammar version <= {1})".format(cut.type, Menu.GrammarVersion)
                    logging.error(message)
                    raise XmlDecoderError(message)
                if not self.menu.cutByName(cut.name):
                    logging.debug("adding cut: %s", cut.__dict__)
                    self.menu.addCut(cut)

    def run_process_objects(self):
        logging.debug("adding object requirements...")
        for objs in self.tables.menu.objects.values():
            for row in [dict(row) for row in objs]:
                name = safe_str(row[kName], "object name")
                type = row[kType]
                threshold = row[kThreshold]
                comparison_operator = row[kComparisonOperator]
                bx_offset = int(row[kBxOffset])
                comment = row.get(kComment, "")
                obj = Algorithm.Object(name, type, threshold, comparison_operator, bx_offset, comment)
                if obj.type not in (types.ObjectTypes + types.SignalTypes):
                    message = "Unsupported object type {0} (grammar version <= {1})".format(obj.type, Menu.GrammarVersion)
                    logging.error(message)
                    raise XmlDecoderError(message)
                if obj.type in types.ObjectTypes:
                    if obj.type not in [scaleSet[kObject] for scaleSet in self.tables.scale.scales]:
                        algorithm = self.menu.algorithmsByObject(obj)[0]
                        message = "Object type `{0}' assigned to algorithm `{1} {2}' is missing in scales set `{3}'".format(obj.type, algorithm.index, algorithm.name, self.tables.scale.scaleSet[kName])
                        logging.error(message)
                        raise XmlDecoderError(message)
                if not obj in self.menu.objects:
                    logging.debug("adding object requirement: %s", obj.__dict__)
                    self.menu.addObject(obj)

    def run_process_externals(self):
        logging.debug("adding external signals...")
        ext_signal_names = [item[kName] for item in self.tables.extSignal.extSignals]
        ext_signal_set_name = self.tables.extSignal.extSignalSet[kName]
        for externals in self.tables.menu.externals.values():
            for row in [dict(row) for row in externals]:
                name = safe_str(row[kName], "external signal name")
                bx_offset = int(row[kBxOffset])
                comment = row.get(kComment, "")
                external = Algorithm.External(name, bx_offset, comment)
                # Verify that all external signals are part of the external signal set.
                if external.signal_name not in ext_signal_names:
                    message = "External signal `{0}' is missing in external signal set `{1}'".format(external.basename, ext_signal_set_name)
                    logging.error(message)
                    raise XmlDecoderError(message)
                if external not in self.menu.externals:
                    logging.debug("adding external signal: %s", external.__dict__)
                    self.menu.addExternal(external)

    def run_process_scales(self):
        logging.debug("adding scales...")
        self.menu.scales = self.tables.scale

    def run_process_ext_signals(self):
        logging.debug("adding external signal sets...")
        self.menu.extSignals = self.tables.extSignal

    def run_verify_menu(self):
        logging.debug("verify menu integrity...")
        self.menu.validate()

def load(filename):
    """Read XML menu from *filename*. Returns menu object."""
    queue = XmlDecoderQueue(filename)
    queue.exec_()
    return queue.menu
