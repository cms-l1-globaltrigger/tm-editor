# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from tmEditor.core.Toolbox import fHex, fCut
from .AbstractTableModel import AbstractTableModel

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['BinsModel', ]

# ------------------------------------------------------------------------------
#  Bins model class
# ------------------------------------------------------------------------------

class BinsModel(AbstractTableModel):
    """Default scale bins table model."""

    def __init__(self, menu, name, parent = None):
        super(BinsModel, self).__init__(menu.scales.bins[name], parent)
        self.name = name
        self.addColumnSpec("Number dec", lambda item: item['number'], int, self.AlignRight)
        self.addColumnSpec("Number hex", lambda item: item['number'], fHex, self.AlignRight)
        self.addColumnSpec("Minimum", lambda item: item['minimum'], fCut, self.AlignRight)
        self.addColumnSpec("Maximum", lambda item: item['maximum'], fCut, self.AlignRight)
        self.addEmptyColumn()
