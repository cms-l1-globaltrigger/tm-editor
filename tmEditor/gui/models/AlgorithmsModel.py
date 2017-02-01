# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from tmEditor.core.Toolbox import fAlgorithm
from tmEditor.core import AlgorithmFormatter
from .AbstractTableModel import AbstractTableModel

from tmEditor.PyQt5Proxy import QtCore

__all__ = ['AlgorithmsModel', ]

# ------------------------------------------------------------------------------
#  Algorithms model class
# ------------------------------------------------------------------------------

class AlgorithmsModel(AbstractTableModel):
    """Default algorithms table model."""

    def __init__(self, menu, parent = None):
        super(AlgorithmsModel, self).__init__(menu.algorithms, parent)
        self.addColumnSpec("Index", lambda item: item.index, int, self.AlignRight)
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Expression", lambda item: item.expression, fAlgorithm)

    def insertRows(self, position, rows, parent = QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.values.append(None)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent = QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            algorithm = self.values[position + i]
            self.values.remove(algorithm)
        self.endRemoveRows()
        return True
