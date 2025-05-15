"""Import XML dialog.

This dialog provides an dialog to import algorithms from another XML file.

Example usage:
>>> dialog = ImportDialog()
>>> dialog.exec_()
>>> print(dialog.algorithms)
>>> print(dialog.cuts)
"""

import logging
from typing import Optional

from PySide6 import QtCore, QtWidgets

from tmEditor.core import XmlDecoder
from tmEditor.core.Menu import Menu

from tmEditor.gui.models import AlgorithmsModel
from tmEditor.gui.Document import TableView

# Common widgets
from tmEditor.gui.CommonWidgets import IconLabel, createIcon
from tmEditor.gui.CommonWidgets import TextFilterWidget

__all__ = ["ImportDialog"]

kName = "name"


class ImportDialog(QtWidgets.QDialog):
    """Dialog providing importing of algorithms from another XML file."""

    def __init__(self, filename: str, menu: Menu, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        # Algorithm selection
        self.menu: Optional[Menu] = None
        self.algorithms: list = []
        self.cuts: list = []
        self.baseMenu: Menu = menu

        self.loadMenu(filename)
        self.validateMenu()

        # Important: sort out all duplicate algorithms !
        if self.menu:
            queue: list = []
            for algorithm in self.menu.algorithms:
                if self.baseMenu.algorithmByName(algorithm.name):
                    queue.append(algorithm)
            for algorithm in queue:
                self.menu.algorithms.remove(algorithm)

        self._setupUi()

    def _setupUi(self) -> None:
        self.setWindowTitle(self.tr("Import"))
        self.setMinimumWidth(500)
        # Filter bar
        self.filterWidget = TextFilterWidget(True, self)
        self.filterWidget.textChanged.connect(self.setFilterText)
        # Table view
        self.tableView = TableView(self)
        self.tableView.setObjectName("importDialogTabelView")
        self.tableView.setStyleSheet("#importDialogTabelView { border: 0; }")
        self.tableView.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        if self.menu:
            model = AlgorithmsModel(self.menu, self)
            proxyModel = QtCore.QSortFilterProxyModel(self)
            proxyModel.setFilterKeyColumn(-1) # Filter all collumns
            proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            proxyModel.setSourceModel(model)
            self.tableView.setModel(proxyModel)
        # Button box
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttonBox.accepted.connect(self.importSelected)
        buttonBox.rejected.connect(self.reject)
        # Create layout.
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.filterWidget)
        layout.addWidget(self.tableView)
        layout.addWidget(IconLabel(createIcon("info"), self.tr("Select available algorithms to import."), self))
        layout.addWidget(buttonBox)
        layout.setStretch(1, 1)
        self.setLayout(layout)

    def setFilterText(self, text: str, /) -> None:
        model = self.tableView.model()
        if isinstance(model, QtCore.QSortFilterProxyModel):
            model.setFilterWildcard(text)

    def loadMenu(self, filename: str) -> None:
        """Load XML menu from file."""
        dialog = QtWidgets.QProgressDialog(self)
        dialog.setWindowTitle(self.tr("Loading..."))
        dialog.setCancelButton(None)
        dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dialog.resize(260, dialog.height())
        dialog.show()
        QtWidgets.QApplication.processEvents()
        try:
            queue = XmlDecoder.XmlDecoderQueue(filename)
            for callback in queue:
                dialog.setLabelText(self.tr("{}...").format(queue.message().capitalize()))
                logging.debug("processing: %s...", queue.message())
                QtWidgets.QApplication.sendPostedEvents(dialog, 0)
                QtWidgets.QApplication.processEvents()
                callback()
                dialog.setValue(queue.progress())
                QtWidgets.QApplication.processEvents()
        except XmlDecoder.XmlDecoderError:
            dialog.close() # make sure to close the progress dialog
            raise
        except Exception:
            dialog.close()
            raise
        dialog.close()
        self.menu = queue.menu

    def validateMenu(self) -> None:
        if self.menu and self.baseMenu:
            if self.menu.scales and self.baseMenu.scales:
                baseScaleSet = self.baseMenu.scales.scaleSet[kName]
                scaleSet = self.menu.scales.scaleSet[kName]
                # Perform more checks
                if scaleSet != baseScaleSet:
                    logging.warning("imported scale set \"%s\" does not match with current scale set \"%s\"", scaleSet, baseScaleSet)
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.tr("Different scale sets"),
                        self.tr("Imported scale set <em>{0}</em> does not match with current scale set <em>{1}</em>, but might be compatible.").format(scaleSet, baseScaleSet),
                    )

    def importSelected(self) -> None:
        """Import selected algorithms and auto adding new cuts."""
        selectedIndexes = self.tableView.selectedIndexes()
        # Make sure something is selected.
        if not selectedIndexes:
            QtWidgets.QMessageBox.warning(
                self,
                self.tr("Empty selection"),
                self.tr("No algorithms are selected to import."),
            )
            return
        if self.menu:
            for index in selectedIndexes:
                if index.column() == 0:
                    # Use the assigned proxy model to map the index.
                    model = self.tableView.model()
                    if isinstance(model, QtCore.QSortFilterProxyModel):
                        index = model.mapToSource(index)
                        algorithm = self.menu.algorithms[index.row()]
                        self.algorithms.append(algorithm)
                        for name in algorithm.cuts():
                            cut = self.menu.cutByName(name)
                            if cut not in self.cuts:
                                self.cuts.append(cut)
        self.accept()
        return
