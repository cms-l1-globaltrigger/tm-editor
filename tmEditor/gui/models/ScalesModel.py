# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from tmEditor.core.Toolbox import fCut
from .AbstractTableModel import AbstractTableModel

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['ScalesModel', ]

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kObject = 'object'
kType = 'type'
kMinimum = 'minimum'
kMaximum = 'maximum'
kStep = 'step'
kNBits = 'n_bits'

# ------------------------------------------------------------------------------
#  Scales model class
# ------------------------------------------------------------------------------

class ScalesModel(AbstractTableModel):
    """Default scales table model."""

    def __init__(self, menu, parent = None):
        super(ScalesModel, self).__init__(menu.scales.scales, parent)
        self.addColumnSpec("Object", lambda item: item[kObject])
        self.addColumnSpec("Type", lambda item: item[kType])
        self.addColumnSpec("Minimum", lambda item: item[kMinimum], fCut, self.AlignRight)
        self.addColumnSpec("Maximum", lambda item: item[kMaximum], fCut, self.AlignRight)
        self.addColumnSpec("Step", lambda item: item[kStep], fCut, self.AlignRight)
        self.addColumnSpec("Bitwidth", lambda item: item[kNBits], int, self.AlignRight)
        self.addEmptyColumn()
