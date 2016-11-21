# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['ScalesModelProxy', ]

# -----------------------------------------------------------------------------
#  Scales model proxy
# -----------------------------------------------------------------------------

class ScalesModelProxy(QtGui.QSortFilterProxyModel):
    """Custom cuts sort/filter proxy."""

    MinimumColumn = 2
    MaximumColumn = 3
    StepColumn = 4
    BitsColumn = 5

    def __init__(self, parent = None):
        super(ScalesModelProxy, self).__init__(parent)

    def lessThan(self, left, right):
        """Custom range sorting."""
        if left.column() in (self.MinimumColumn, self.MaximumColumn, self.StepColumn, self.BitsColumn):
            try:
                return self.__toFloat(left) < self.__toFloat(right)
            except ValueError:
                pass
        return super(ScalesModelProxy, self).lessThan(left, right)

    def __toFloat(self, index):
        return float(self.sourceModel().data(index, QtCore.Qt.DisplayRole))
