# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

import tmTable
import tmGrammar

import Toolbox
from tmEditor.core.Settings import MaxAlgorithms
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxValidator, AlgorithmSyntaxError

from distutils.version import StrictVersion

import logging
import uuid
import sys, os

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

class XmlEncoderError(Exception):
    """Exeption for XML encoder errors."""
    def __init__(self, message):
        super(XmlEncoderError, self).__init__(message)

def safe_str(s):
    """Returns safe version of string. The function strips:
     * whitespaces, tabulators
     * newlines, carriage returns
     * NULL characters
    """
    return str(s).strip(" \t\n\r\x00")

def test_permissions(filename):
    """Test if target filename is writeable by the user."""
    if not os.path.isfile(filename):
        filename = os.path.dirname(filename)
    if not os.access(filename, os.W_OK):
        message = "permission denied `{0}`".format(filename)
        logging.error(message)
        raise RuntimeError(message)

def dump(menu, filename):
    """Write XML menu to *filename*. This regenerates the UUID."""
    filename = os.path.abspath(filename)

    logging.debug("preparing menu to write to `%s`", filename)

    # WORKAROUND (menu2xml() will not fail on permission denied)
    test_permissions(filename)

    pwd = os.getcwd()
    os.chdir(Toolbox.getXsdDir())

    try:

        # Create a new menu instance.
        menu_table = tmTable.Menu()

        # Regenerate UUID and version
        menu.menu.regenerate()
        logging.debug("regenerated menu UUID to: %s", menu.menu.uuid_menu)
        logging.debug("updated grammar version to: %s", menu.menu.grammar_version)

        # Menu inforamtion
        menu_table.menu[kName] = safe_str(menu.menu.name)
        menu_table.menu[kComment] = safe_str(menu.menu.comment)
        menu_table.menu[kUUIDMenu] = menu.menu.uuid_menu
        menu_table.menu[kUUIDFirmware] = DEFAULT_UUID
        menu_table.menu[kGrammarVersion] = menu.menu.grammar_version
        menu_table.menu[kNModules] = "0"
        menu_table.menu[kIsValid] = "1"
        menu_table.menu[kIsObsolete] = "0"
        menu_table.menu[kAncestorId] = "0"
        menu_table.menu[kGlobalTag] = ""

        logging.debug("menu information: %s", dict(menu_table.menu))

        for algorithm in menu.algorithms:
            # Create algorithm row
            row = tmTable.Row()
            row[kIndex] = str(algorithm.index)
            row[kModuleId] = "0"
            row[kModuleIndex] = str(algorithm.index)
            row[kName] = safe_str(algorithm.name)
            row[kExpression] = AlgorithmFormatter.compress(algorithm.expression)
            row[kComment] = algorithm.comment
            # Validate algorithm row
            if not tmTable.isAlgorithm(row):
                message = "invalid algorithm ({algorithm.index}): {algorithm.name}".format(algorithm=algorithm)
                logging.error(message)
                raise RuntimeError(message)
            # Append algorithm row
            logging.debug("appending algorithm: %s", dict(row))
            menu_table.algorithms.append(row)

            # Objects
            if algorithm.name not in menu_table.objects.keys():
                menu_table.objects[algorithm.name] = []
            for name in algorithm.objects():
                object_ = menu.objectByName(name)
                if not object_:
                    message = "missing object requirement: {0}".format(name)
                    logging.error(message)
                    raise RuntimeError(message)
                # Create object row
                row = tmTable.Row()
                row[kName] = safe_str(object_.name)
                row[kType] = object_.type
                row[kThreshold] = safe_str(format(object_.decodeThreshold(), FORMAT_FLOAT))
                row[kComparisonOperator] = object_.comparison_operator
                row[kBxOffset] = str(object_.bx_offset)
                # Validate object row
                if not tmTable.isObjectRequirement(row):
                    message = "invalid object requirement: {0}".format(name)
                    logging.error(message)
                    raise RuntimeError(message)
                # Append object trow
                logging.debug("appending object requirement: %s", dict(row))
                menu_table.objects[algorithm.name] = menu_table.objects[algorithm.name] + (row, )

            # Externals
            if algorithm.name not in menu_table.externals.keys():
                menu_table.externals[algorithm.name] = []
            for name in algorithm.externals():
                external = menu.externalByName(name)
                if not external:
                    message = "missing external signal: {0}".format(name)
                    logging.error(message)
                    raise RuntimeError(message)
                # Create external row
                row = tmTable.Row()
                row[kName] = safe_str(external.name)
                row[kBxOffset] = str(external.bx_offset)
                # Validate external row
                if not tmTable.isExternalRequirement(row):
                    message = "invalid external signal: {0}".format(name)
                    logging.error(message)
                    raise RuntimeError(message)
                # Append external row
                logging.debug("appending external signal: %s", dict(row))
                menu_table.externals[algorithm.name] = menu_table.externals[algorithm.name] + (row, )

            # Cuts
            if algorithm.name not in menu_table.cuts.keys():
                menu_table.cuts[algorithm.name] = []
            for name in algorithm.cuts():
                cut = menu.cutByName(name)
                if not cut:
                    message = "missing cut: {0}".format(name)
                    logging.error(message)
                    raise RuntimeError(message)
                # Create cut row
                row = tmTable.Row()
                row[kName] = safe_str(cut.name)
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
                    raise RuntimeError(message)
                # Append cut row
                logging.debug("appending cut: %s", dict(row))
                menu_table.cuts[algorithm.name] = menu_table.cuts[algorithm.name] + (row, )

        # Write to XML file.
        logging.debug("writing XML file to `%s'", filename)
        tmTable.menu2xml(menu_table, menu.scales, menu.extSignals, filename)
        # WORKAROUND (check if file was written)
        if not os.path.isfile(filename):
            message = "failed to write to file `{0}'".format(filename)
            logging.error(message)
            raise RuntimeError(message)

    except:
        os.chdir(pwd)
        raise
