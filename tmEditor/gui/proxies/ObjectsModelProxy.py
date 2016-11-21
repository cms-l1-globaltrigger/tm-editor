# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from tmEditor.core.Menu import toObject

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['ObjectsModelProxy', ]

# -----------------------------------------------------------------------------
#  Objects model proxy
# -----------------------------------------------------------------------------

class ObjectsModelProxy(QtGui.QSortFilterProxyModel):
    """Custom objects sort/filter proxy."""

    NameColumn = 0
    ThresholdColumn = 3
    BxOffsetColumn = 4

    def __init__(self, parent = None):
        super(ObjectsModelProxy, self).__init__(parent)

    def lessThan(self, left, right):
        """Custom object sorting."""
        # Sort objects by their custom comparison function.
        if left.column() == self.NameColumn:
            return self.__toObject(left) < self.__toObject(right)
        if left.column() == self.ThresholdColumn:
            return float(self.sourceModel().data(left, QtCore.Qt.DisplayRole).split()[0]) < \
                float(self.sourceModel().data(right, QtCore.Qt.DisplayRole).split()[0])
        if left.column() == self.BxOffsetColumn:
            return int(self.sourceModel().data(left, QtCore.Qt.DisplayRole)) < int(self.sourceModel().data(right, QtCore.Qt.DisplayRole))
        return super(QtGui.ObjectsModelProxy, self).lessThan(left, right)

    def __toObject(self, index):
        return toObject(self.sourceModel().data(index, QtCore.Qt.DisplayRole))
