# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

import tmTable
import tmGrammar

import Menu
import Algorithm
import Toolbox
import Types
from tmEditor.core.Settings import MaxAlgorithms
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError

from distutils.version import StrictVersion

import logging
import sys, os

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

class XmlDecoderError(Exception):
    """Exeption for XML decoder errors."""
    def __init__(self, message):
        super(XmlDecoderError, self).__init__(message)

def safe_str(s):
    """Returns safe version of string. The function strips:
     * whitespaces, tabulators
     * newlines, carriage returns
     * NULL characters
    """
    return s.strip(" \t\n\r\x00")

def patch_cut(cut):
    """Patch old specification."""
    if cut.object == tmGrammar.comb and cut.type == tmGrammar.CHGCOR:
        if cut.data == "0":
            cut.data = "ls"
        if cut.data == "1":
            cut.data = "os"

def verify_grammar_version(menu_table):
    """Verify menu grammar version."""
    if kGrammarVersion not in menu_table.menu.keys():
        message = "Missing grammar version, corrupted file?"
        logging.error(message)
        raise XmlDecoderError(message)
    version = menu_table.menu[kGrammarVersion]
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

def load(filename):
    """Read XML menu from *filename*. Returns menu object."""
    filename = os.path.abspath(filename)

    # Check file accessible
    if not os.path.isfile(filename):
        message = "No such file or directory `{0}'".format(filename)
        logging.error(message)
        raise XmlDecoderError(message)

    # Load tables from XML file.
    menu_table = tmTable.Menu()
    scale_table = tmTable.Scale()
    ext_signal_table = tmTable.ExtSignal()

    # Read from XML file.
    logging.debug("Reading XML file from `%s'", filename)
    warnings = tmTable.xml2menu(filename, menu_table, scale_table, ext_signal_table)

    if warnings:
        message = "Failed to read XML menu `{0}'\n{1}".format(filename, warnings)
        logging.error(message)
        raise XmlDecoderError(message)

    # Verify grammar version.
    verify_grammar_version(menu_table)

    # Populate the containers.
    menu = Menu.Menu()
    menu.menu.name = safe_str(menu_table.menu[kName])
    menu.menu.comment = menu_table.menu[kComment] if kComment in menu_table.menu else ""
    menu.menu.uuid_menu = menu_table.menu[kUUIDMenu]
    menu.menu.grammar_version = menu_table.menu[kGrammarVersion]

    logging.debug("loaded menu information: %s", menu.menu.__dict__)

    # Add algorithms
    for row in [dict(row) for row in menu_table.algorithms]:
        index = int(row[kIndex])
        name = safe_str(row[kName])
        expression = row[kExpression]
        comment = row.get(kComment, "")
        algorithm = Algorithm.Algorithm(index, name, expression, comment)
        logging.debug("adding algorithm: %s", algorithm.__dict__)
        menu.addAlgorithm(algorithm)
    # Add cuts
    for cuts in menu_table.cuts.values():
        for row in [dict(row) for row in cuts]:
            name = safe_str(row[kName])
            object = row[kObject]
            type = row[kType]
            minimum = float(row[kMinimum])
            maximum = float(row[kMaximum])
            data = row[kData]
            comment = row.get(kComment, "")
            cut = Algorithm.Cut(name, object, type, minimum, maximum, data, comment)
            # Patch old formats
            patch_cut(cut)
            if cut.type not in Types.CutTypes:
                message = "Unsupported cut type {0} (grammar version <= {1})".format(cut.type, Menu.GrammarVersion)
                logging.error(message)
                raise XmlDecoderError(message)
            if not menu.cutByName(cut.name):
                logging.debug("adding cut: %s", cut.__dict__)
                menu.addCut(cut)
    # Add objects
    for objs in menu_table.objects.values():
        for row in [dict(row) for row in objs]:
            name = safe_str(row[kName])
            type = row[kType]
            threshold = row[kThreshold]
            comparison_operator = row[kComparisonOperator]
            bx_offset = int(row[kBxOffset])
            comment = row.get(kComment, "")
            obj = Algorithm.Object(name, type, threshold, comparison_operator, bx_offset, comment)
            if obj.type not in Types.ObjectTypes:
                message = "Unsupported object type {0} (grammar version <= {1})".format(obj.type, Menu.GrammarVersion)
                logging.error(message)
                raise XmlDecoderError(message)
            if obj.type not in [scaleSet[kObject] for scaleSet in scale_table.scales]:
                algorithm = menu.algorithmsByObject(obj)[0]
                message = "Object type `{0}' assigned to algorithm `{1} {2}' is missing in scales set `{3}'".format(obj.type, algorithm.index, algorithm.name, scale.scaleSet[kName])
                logging.error(message)
                raise XmlDecoderError(message)
            if not obj in menu.objects:
                logging.debug("adding object requirement: %s", obj.__dict__)
                menu.addObject(obj)
    # Add external signals
    ext_signal_names = [item[kName] for item in ext_signal_table.extSignals]
    ext_signal_set_name = ext_signal_table.extSignalSet[kName]
    for externals in menu_table.externals.values():
        for row in [dict(row) for row in externals]:
            name = safe_str(row[kName])
            bx_offset = int(row[kBxOffset])
            comment = row.get(kComment, "")
            external = Algorithm.External(name, bx_offset, comment)
            # Verify that all external signals are part of the external signal set.
            if external.signal_name not in ext_signal_names:
                algorithm = menu.algorithmsByExternal(external)[0]
                message = "External signal `{0}' assigned to algorithm `{1} {2}' is missing in external signal set `{3}'".format(external.basename, algorithm.index, algorithm.name, ext_signal_set_name)
                logging.error(message)
                raise XmlDecoderError(message)
            if external not in menu.externals:
                logging.debug("adding external signal: %s", external.__dict__)
                menu.addExternal(external)
    logging.debug("adding scales")
    menu.scales = scale_table
    logging.debug("adding external signal sets")
    menu.extSignals = ext_signal_table

    return menu
