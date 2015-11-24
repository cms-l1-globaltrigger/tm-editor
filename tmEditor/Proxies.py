# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Sort and filter proxies for custom models.
"""

from tmEditor.Menu import toObject, toExternal

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ["ObjectsModelProxy", "CutsModelProxy", "ExternalsModelProxy"]

#
# Objects model proxy
#

class ObjectsModelProxy(QSortFilterProxyModel):
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
            return float(self.sourceModel().data(left, Qt.DisplayRole).split()[0]) < \
                float(self.sourceModel().data(right, Qt.DisplayRole).split()[0])
        if left.column() == self.BxOffsetColumn:
            return int(self.sourceModel().data(left, Qt.DisplayRole)) < int(self.sourceModel().data(right, Qt.DisplayRole))
        return super(ObjectsModelProxy, self).lessThan(left, right)

    def __toObject(self, index):
        return toObject(self.sourceModel().data(index, Qt.DisplayRole))

#
# Cuts model proxy
#

class CutsModelProxy(QSortFilterProxyModel):
    """Custom cuts sort/filter proxy."""

    MinimumColumn = 3
    MaximumColumn = 4

    def __init__(self, parent = None):
        super(CutsModelProxy, self).__init__(parent)

    def lessThan(self, left, right):
        """Custom cut sorting."""
        if left.column() in (self.MinimumColumn, self.MaximumColumn):
            try:
                return self.__toFloat(left) < self.__toFloat(right)
            except ValueError:
                pass
        return super(CutsModelProxy, self).lessThan(left, right)

    def __toFloat(self, index):
        return float(self.sourceModel().data(index, Qt.DisplayRole))

#
# Objects model proxy
#

class ExternalsModelProxy(QSortFilterProxyModel):
    """Custom externals sort/filter proxy."""

    NameColumn = 0
    BxOffsetColumn = 1

    def __init__(self, parent = None):
        super(ExternalsModelProxy, self).__init__(parent)

    def lessThan(self, left, right):
        """Custom object sorting."""
        # Sort externals by their custom comparison function.
        if left.column() == self.NameColumn:
            return self.__toExternal(left) < self.__toExternal(right)
        if left.column() == self.BxOffsetColumn:
            return int(self.__toExternal(left).bx_offset) < int(self.__toExternal(right).bx_offset)
        return super(ExternalsModelProxy, self).lessThan(left, right)

    def __toExternal(self, index):
        return toExternal(self.sourceModel().data(index, Qt.DisplayRole))
