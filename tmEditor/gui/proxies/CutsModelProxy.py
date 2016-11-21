# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['CutsModelProxy', ]

# -----------------------------------------------------------------------------
#  Cuts model proxy
# -----------------------------------------------------------------------------

class CutsModelProxy(QtGui.QSortFilterProxyModel):
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
