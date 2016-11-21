# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from tmEditor.core.Toolbox import fBxOffset, miniIcon
from .AbstractTableModel import AbstractTableModel

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['ExternalsModel', ]

# ------------------------------------------------------------------------------
#  Externals model class
# ------------------------------------------------------------------------------

class ExternalsModel(AbstractTableModel):
    """Default external siganls requirements table model."""

    def __init__(self, menu, parent = None):
        super(ExternalsModel, self).__init__(menu.externals, parent)
        self.addColumnSpec("Name", lambda item: item.name, decoration=miniIcon('default'))
        self.addColumnSpec("BX Offset", lambda item: item.bx_offset, fBxOffset, self.AlignRight)
        self.addEmptyColumn()
