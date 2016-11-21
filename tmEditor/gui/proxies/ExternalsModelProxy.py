# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from tmEditor.core.Menu import toExternal

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['ExternalsModelProxy', ]


# -----------------------------------------------------------------------------
#  Externals model proxy
# -----------------------------------------------------------------------------

class ExternalsModelProxy(QtGui.QSortFilterProxyModel):
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
        return toExternal(self.sourceModel().data(index, QtCore.Qt.DisplayRole))
