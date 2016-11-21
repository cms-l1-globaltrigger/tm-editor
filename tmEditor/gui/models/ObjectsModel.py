# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

import tmGrammar

from tmEditor.core.Toolbox import fComparison, fThreshold, fBxOffset, miniIcon
from .AbstractTableModel import AbstractTableModel

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['ObjectsModel', ]

# ------------------------------------------------------------------------------
#  Objects model class
# ------------------------------------------------------------------------------

class ObjectsModel(AbstractTableModel):
    """Default object requirements table model."""

    def __init__(self, menu, parent = None):
        super(ObjectsModel, self).__init__(menu.objects, parent)
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Type", lambda item: item.type)
        self.addColumnSpec("", lambda item: item.comparison_operator, fComparison, headerToolTip="Comparison", headerDecoration=QtGui.QIcon(":/icons/compare.svg"), headerSizeHint=QtCore.QSize(26, -1))
        self.addColumnSpec("Threshold", lambda item: item.threshold, fThreshold, self.AlignRight)
        self.addColumnSpec("BX Offset", lambda item: item.bx_offset, fBxOffset, self.AlignRight)
        self.addEmptyColumn()

    def data(self, index, role):
        """Overloaded for experimental icon decoration."""
        if index.isValid():
            columnSpec = self.columnSpecs[index.column()]
            value = self.values[index.row()]
            if columnSpec:
                if columnSpec.title == "Name":
                    if role == QtCore.Qt.DecorationRole:
                        return miniIcon(value.type.lower())
                # Override display for count type objects (no decimals, no GeV suffix)
                if columnSpec.title == "Threshold":
                    if role == QtCore.Qt.DisplayRole:
                        if value.type in (tmGrammar.MBT0HFP, tmGrammar.MBT1HFP, tmGrammar.MBT0HFM, tmGrammar.MBT1HFM, tmGrammar.TOWERCOUNT):
                            return "{0:.0f} counts".format(float(value.threshold)) # return integer string!
        return super(ObjectsModel, self).data(index, role)
