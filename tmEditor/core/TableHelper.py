# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Helper class for tmTable module."""

import tmTable

class TableHelper(object):
    def __init__(self):
        self.reset()

    def reset(self):
        """Clear tables contents."""
        self.menu = tmTable.Menu()
        self.scale = tmTable.Scale()
        self.extSignal = tmTable.ExtSignal()

    def load(self, filename):
        """Load tables from XML file."""
        self.reset()
        return tmTable.xml2menu(filename, self.menu, self.scale, self.extSignal)

    def dump(self, filename):
        """Dump tables to XML file."""
        tmTable.menu2xml(self.menu, self.scale, self.extSignal, filename)
