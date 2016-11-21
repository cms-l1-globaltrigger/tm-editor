# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from PyQt4 import QtCore
from PyQt4 import QtGui

# ------------------------------------------------------------------------------
#  Common table view widget
# ------------------------------------------------------------------------------

class TableView(QtGui.QTableView):
    """Common sortable table view wiget."""

    def __init__(self, parent=None):
        """@param parent optional parent widget.
        """
        super(TableView, self).__init__(parent)
        # Setup table view.
        self.setShowGrid(False)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        # Setup horizontal column appearance.
        horizontalHeader = self.horizontalHeader()
        horizontalHeader.setHighlightSections(False)
        horizontalHeader.setResizeMode(QtGui.QHeaderView.Interactive)
        horizontalHeader.setStretchLastSection(True)
        # Setup vertical row appearance.
        verticalHeader = self.verticalHeader()
        verticalHeader.setResizeMode(QtGui.QHeaderView.Fixed)
        verticalHeader.setDefaultSectionSize(20)
        verticalHeader.hide()
        self.setSortingEnabled(True)

    def currentMappedIndex(self):
        """@returns current selected proxy mapped index, else None."""
        # Get the current selected table view index.
        index = self.selectedIndexes()
        if index:
            # Use the assigned proxy model to map the index.
            return self.model().mapToSource(index[0])
