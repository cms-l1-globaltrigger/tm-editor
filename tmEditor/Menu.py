# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Menu container, wrapping tmTable and XML bindings.
"""

import tmTable
import tmGrammar

from tmEditor import Toolbox

import uuid
import shutil
import tempfile
import logging
import sys, os

__all__ = ['Menu', ]

class Menu(object):
    """L1-Trigger Menu container class."""

    def __init__(self, filename = None):
        self.menu = {}
        self.algorithms = []
        self.cuts = []
        self.objects = []
        self.scales = None
        self.externals = None
        if filename:
            self.loadXml(filename)

    def addObject(self, name, offset = 0):
        """Provided for convenience."""
        self.objects.append(Object(
            name = name,
            bx_offset = offset,
        ))

    def addCut(self, name, minimum, maximum):
        """Provided for convenience."""
        self.objects.append(Cut(
            name = name,
            minimum = minimum,
            maximum = maximum,
        ))

    def addAlgorithm(self, name, expression):
        """Provided for convenience."""
        self.objects.append(Algorithm(
            name = name,
            expression = expression,
        ))

    def loadXml(self, filename):
        """Provided for convenience."""
        menu, scale, ext_signal = loadXml(filename)
        self.menu = dict(menu.menu.items())
        self.algorithms = [Algorithm(algorithm) for algorithm in menu.algorithms]
        buffer = []
        for cuts in menu.cuts.values():
            for cut in cuts:
                cut = Cut(cut.items())
                if not cut in buffer:
                    buffer.append(cut)
        self.cuts = buffer
        buffer = []
        for objs in menu.objects.values():
            for obj in objs:
                obj = Object(obj.items())
                if not obj in buffer:
                    buffer.append(obj)
        self.objects = buffer
        buffer = []
        for externals in menu.externals.values():
            for external in externals:
                external = External(external.items())
                if not external in buffer:
                    buffer.append(external)
        self.externals = buffer
        self.scales = scale
        self.extSignals = ext_signal

    def saveXml(self, filename):
        """Provided for convenience."""
        # Regenerate menu UUID.
        self.menu['uuid_menu'] = str(uuid.uuid4())
        # Reset firmware UUID.
        self.menu['uuid_firmware'] = '00000000-0000-0000-0000-000000000000'
        # Create a new menu instance.
        menu = tmTable.Menu()
        for key, value in self.menu.items():
            menu.menu[key] = str(value)
        for algorithm in self.algorithms:

            print algorithm
            print algorithm.objects()
            print algorithm.cuts()

            row = tmTable.Row()
            for key, value in algorithm.items():
                row[key] = str(value)
                menu.algorithms.append(row)

            # OBJECTS
            if algorithm['name'] not in menu.objects:
                menu.objects[algorithm['name']] = []

            # TODO

            # for key_algo, table_algo in self.list_panel.algorithm.data.iteritems():
            #   if not isinstance(table_algo, AlgorithmModel.Table): continue
            #   for ii in range(len(table_algo.data)):
            #     algorithm = table_algo.data[ii]
            #     row = tmTable.Row()
            #     for key, value in algorithm.GetDict().iteritems():
            #       row[key] = str(value)
            #     row["index"] = str(ii+1)
            #     menu.algorithms.append(row)
            #
            #     name = row["name"]
            #     elements = item_in_algo[name]
            #
            #     ## OBJECTS
            #     if name not in menu.objects:
            #       menu.objects[name] = []
            #     for key_obj, table_obj in self.list_panel.object.data.iteritems():
            #       if not isinstance(table_obj, ObjectModel.Table): continue
            #       for jj in range(len(table_obj.data)):
            #         object = table_obj.data[jj]
            #         row = tmTable.Row()
            #         for key, value in object.GetDict().iteritems():
            #           row[key] = str(value)
            #         if DISABLE_UNUSED and row["name"] not in elements: continue
            #
            #         row["threshold"] = "%+23.16E" % float(row["threshold"])
            #         key = ObjectModel.GetKey(row["type"])
            #         if hasattr(self, 'table_scale') and key in self.table_scale.bins:
            #           bins_round = common.GetBins(self.table_scale.bins, key)
            #           bins = common.GetBins(self.table_scale.bins, key, "%+23.16E")
            #           index = bins_round.index("%g" % float(row["threshold"]))
            #           row["threshold"] = bins[index]
            #         menu.objects[name] = menu.objects[name] + (row,)
            #
            #     ## EXTERNALS
            #     if name not in menu.externals:
            #       menu.externals[name] = []
            #     for key_ext, table_ext in self.list_panel.ext_req.data.iteritems():
            #       if not isinstance(table_ext, ExtReqModel.Table): continue
            #       for jj in range(len(table_ext.data)):
            #         object = table_ext.data[jj]
            #         row = tmTable.Row()
            #         for key, value in object.GetDict().iteritems():
            #           row[key] = str(value)
            #         if DISABLE_UNUSED and row["name"] not in elements: continue
            #
            #         menu.externals[name] = menu.externals[name] + (row,)
            #
            #
            #     ## CUTS
            #     if name not in menu.cuts:
            #       menu.cuts[name] = []
            #     for key_cut, table_cut in self.list_panel.cut.data.iteritems():
            #       if not isinstance(table_cut, CutModel.Table): continue
            #       for jj in range(len(table_cut.data)):
            #         cut = table_cut.data[jj]
            #         row = tmTable.Row()
            #         for key, value in cut.GetDict().iteritems():
            #           row[key] = str(value)
            #         if DISABLE_UNUSED and row["name"] not in elements: continue
            #
            #         for key in ["minimum", "maximum"]:
            #           row[key] = "%+23.16E" % float(row[key])
            #           scale = CutModel.GetKey(row["object"], row["type"])
            #           if hasattr(self, 'table_scale') and scale in self.table_scale.bins:
            #             bins_round = common.GetBins(self.table_scale.bins, scale)
            #             bins = common.GetBins(self.table_scale.bins, scale, "%+23.16E")
            #             index = bins_round.index("%g" % float(row[key]))
            #             row[key] = bins[index]
            #
            #         menu.cuts[name] = menu.cuts[name] + (row,)
        # # EXTERNALS
        #     if algorithm['name'] not in menu.externals:
        #         menu.externals[algorithm['name']] = []
        #     for key_ext, table_ext in self.list_panel.ext_req.data.iteritems():
        #   if not isinstance(table_ext, ExtReqModel.Table): continue
        #   for jj in range(len(table_ext.data)):
        #     object = table_ext.data[jj]
        #     row = tmTable.Row()
        #     for key, value in object.GetDict().iteritems():
        #       row[key] = str(value)
        #     if DISABLE_UNUSED and row["name"] not in elements: continue
        #
        #     menu.externals[name] = menu.externals[name] + (row,)

        # Write menu, scales and external signals to file.
        # TODO # saveXml(filename, menu, self.scales, self.extSignals)

# ------------------------------------------------------------------------------
#  Algorithm's container class.
# ------------------------------------------------------------------------------

class Algorithm(dict):
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
        externals = set()
        # TODO thats even more tricky... should be part of the parser... oO'
        return list(externals)

# ------------------------------------------------------------------------------
#  Cut's container class.
# ---------------------        for token in self.tokens():
            for name in tmGrammar.objectName:
                if
            if token in ---------------------------------------------------------

class Cut(dict):
    @property
    def name(self):
        return self['name']

# ------------------------------------------------------------------------------
#  Object's container class.
# ------------------------------------------------------------------------------

class Object(dict):
    @property
    def name(self):
        return self['name']

# ------------------------------------------------------------------------------
#  External's contianer class.
# ------------------------------------------------------------------------------

class External(dict):
    @property
    def name(self):
        return self['name']

# ------------------------------------------------------------------------------
#  TODO take care of creation/destruction of virtual environment by dedicated class.
# ------------------------------------------------------------------------------

def loadXml(filename, location = Toolbox.getenv('TMGUI_DIR')):
    """Creates a temporary directory, copies the XML and creates symbolic
    links to the XSD files, then loads and validates the menu. Returns a
    tuple containing table objects for menu, scales and external signals.

    XML parsing requires that the XSD files are in the same directory as
    the XML file (this location is actually specified in the XML's header).
    As this prevents to load an XML file at any other location than the XSD
    directory a convenient solution is to create a save temporary directory
    and create a symbolic link to the XML file as well as symbolic links to
    any dependent XSD files. Using only symbolic links does not require to
    copy any file content preserving full data integrity.

    /tmp/tmpPAMK9j/L1Menu_Sample.xml --> /home/user/L1Menu_Sample.xml
    /tmp/tmpPAMK9j/xsd-type --> /usr/shared/utm/xsd-type
    /tmp/tmpPAMK9j/menu.xsd --> /usr/shared/utm/menu.xsd
    """
    logging.debug("Toolbox.loadXml(filename=\"%s\", location=\"%s\")", filename, location)

    # Get absolute path to source filename.
    filename = os.path.abspath(filename)
    logging.debug("loading XML file `%s'", filename)

    # Create a temporary directory and change current location.
    tmpdir = tempfile.mkdtemp()
    logging.debug("created temporary location `%s'", tmpdir)
    cwd = os.getcwd()
    os.chdir(tmpdir)

    # Create symbolic links to XML and XSD files (src, dest).
    symlinks = (
        (filename, os.path.basename(filename)),
        (os.path.join(location, 'xsd-type'), 'xsd-type'),
        (os.path.join(location, 'menu.xsd'), 'menu.xsd'),
    )
    for src, dest in symlinks:
        os.symlink(src, dest)
        logging.debug("created symbolic link `%s' -> `%s'", src, dest)

    # Load tables from XML file.
    menu = tmTable.Menu()
    scale = tmTable.Scale()
    ext_signal = tmTable.ExtSignal()

    logging.debug("reading XML file from `%s'", filename)
    warnings = tmTable.xml2menu(os.path.basename(filename), menu, scale, ext_signal)

    # Unlink all symbolic links.
    for _, dest in symlinks:
        logging.debug("removing symbolic link `%s'", os.path.join(tmpdir, dest))
        os.unlink(dest)

    # Change back to current working directory.
    os.chdir(cwd)

    # Remove temporary directory.
    logging.debug("removing temporary location `%s'", tmpdir)
    shutil.rmtree(tmpdir)

    # Handle errors only after removing the temporary files.
    if warnings:
        raise RuntimeError("Failed to load XML menu {filename}\n{warnings}".format(**locals()))

    return menu, scale, ext_signal

# ------------------------------------------------------------------------------
#  TODO take care of creation/destruction of virtual environment by dedicated class.
# ------------------------------------------------------------------------------

def saveXml(filename, menu, scale, ext_signal, location = Toolbox.getenv('TMGUI_DIR')):
    """Creates a temporary directory, copies the XML and creates symbolic
    links to the XSD files, then loads and validates the menu. Returns a
    tuple containing table objects for menu, scales and external signals.

    XML parsing requires that the XSD files are in the same directory as
    the XML file (this location is actually specified in the XML's header).
    As this prevents to load an XML file at any other location than the XSD
    directory a convenient solution is to create a save temporary directory
    and create a symbolic link to the XML file as well as symbolic links to
    any dependent XSD files. Using only symbolic links does not require to
    copy any file content preserving full data integrity.

    /tmp/tmpPAMK9j/L1Menu_Sample.xml --> /home/user/L1Menu_Sample.xml
    /tmp/tmpPAMK9j/xsd-type --> /usr/shared/utm/xsd-type
    /tmp/tmpPAMK9j/menu.xsd --> /usr/shared/utm/menu.xsd
    """
    logging.debug("Toolbox.saveXml(filename=\"%s\", menu=\"%s\", scale=\"%s\", ext_signal=\"%s\", location=\"%s\")", menu, scale, ext_signal, location)

    # Get absolute path to source filename.
    filename = os.path.abspath(filename)
    logging.debug("writing to XML file `%s'", filename)

    # Create a temporary directory and change current location.
    tmpdir = tempfile.mkdtemp()
    logging.debug("created temporary location `%s'", tmpdir)
    cwd = os.getcwd()
    os.chdir(tmpdir)

    # Create symbolic links to XML and XSD files (src, dest).
    symlinks = (
        (filename, os.path.basename(filename)),
        (os.path.join(location, 'xsd-type'), 'xsd-type'),
        (os.path.join(location, 'menu.xsd'), 'menu.xsd'),
    )
    for src, dest in symlinks:
        os.symlink(src, dest)
        logging.debug("created symbolic link `%s' -> `%s'", src, dest)

    logging.debug("writing XML file to `%s'", filename)
    warnings = tmTable.menu2xml(menu, scale, ext_signal, os.path.basename(filename))

    # Unlink all symbolic links.
    for _, dest in symlinks:
        logging.debug("removing symbolic link `%s'", os.path.join(tmpdir, dest))
        os.unlink(dest)

    # Change back to current working directory.
    os.chdir(cwd)

    # Remove temporary directory.
    logging.debug("removing temporary location `%s'", tmpdir)
    shutil.rmtree(tmpdir)

    # Handle errors only after removing the temporary files.
    if warnings:
        raise RuntimeError("Failed to save XML menu {filename}\n{warnings}".format(**locals()))
