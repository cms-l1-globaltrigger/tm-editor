"""Table view."""

from typing import Optional

from PyQt5 import QtCore, QtWidgets

# ------------------------------------------------------------------------------
#  Common table view widget
# ------------------------------------------------------------------------------

class TableView(QtWidgets.QTableView):
    """Common sortable table view wiget."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self.setShowGrid(False)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)

        horizontalHeader = self.horizontalHeader()
        horizontalHeader.setHighlightSections(False)
        horizontalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        horizontalHeader.setStretchLastSection(True)

        verticalHeader = self.verticalHeader()
        verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        verticalHeader.setDefaultSectionSize(20)
        verticalHeader.hide()

        self.setSortingEnabled(True)

    def currentMappedIndex(self) -> Optional[QtCore.QModelIndex]:
        """@returns current selected proxy mapped index, else None."""
        # Get the current selected table view index.
        index = self.selectedIndexes()
        if index:
            # Use the assigned proxy model to map the index.
            return self.model().mapToSource(index[0])  # type: ignore
        return None
