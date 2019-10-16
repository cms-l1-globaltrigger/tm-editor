# -*- coding: utf-8 -*-

from PyQt5 import QtCore

__all__ = ['CutsModelProxy', ]

# -----------------------------------------------------------------------------
#  Cuts model proxy
# -----------------------------------------------------------------------------

class CutsModelProxy(QtCore.QSortFilterProxyModel):
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
        return float(self.sourceModel().data(index, QtCore.Qt.DisplayRole))
