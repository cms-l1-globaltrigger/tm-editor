# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Import XML dialog.

This dialog provides an dialog to import algorithms from another XML file.

Example usage:
>>> dialog = ImportDialog()
>>> dialog.exec_()
>>> print dialog.algorithms
>>> print dialog.cuts
"""

from tmEditor.Models import AlgorithmsModel
from tmEditor.Document import TableView
from tmEditor.Menu import Menu
from tmEditor import Toolbox
from tmEditor.AlgorithmEditor import MaxAlgorithms

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['ImportDialog', ]

class ImportDialog(QDialog):
    """Dialog providing importing of algorithms from another XML file."""

    def __init__(self, filename, menu, parent = None):
        super(ImportDialog, self).__init__(parent)
        # Dialog appeareance
        self.setWindowTitle(self.tr("Import"))
        self.setMinimumWidth(500)
        # Algorithm selection
        self.algorithms = []
        self.cuts = []
        self.baseMenu = menu
        self.menu = Menu(filename)
        if self.menu.scales.scaleSet['name'] != self.baseMenu.scales.scaleSet['name']:
            QMessageBox.warning(self,
                self.tr("Different scale sets"),
                QString("Unable to import from <em>%1</em> as scale sets do not match.").arg(filename),
            )
        # Important: sort out all duplicate algorithms !
        queue = []
        for algorithm in self.menu.algorithms:
            if self.baseMenu.algorithmByName(algorithm.name):
                queue.append(algorithm)
        for algorithm in queue:
            self.menu.algorithms.remove(algorithm)
        model = AlgorithmsModel(self.menu, self)
        proxyModel = QSortFilterProxyModel(self)
        proxyModel.setSourceModel(model)
        self.tableView = TableView(self)
        self.tableView.setObjectName("importDialogTabelView")
        self.tableView.setStyleSheet("#importDialogTabelView { border: 0; }")
        self.tableView.setModel(proxyModel)
        self.tableView.sortByColumn(0, Qt.AscendingOrder)
        # Button box
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self._import)
        buttonBox.rejected.connect(self.reject)
        # Create layout.
        layout = QGridLayout()
        layout.addWidget(self.tableView)
        layout.addWidget(Toolbox.IconLabel(Toolbox.createIcon("info"), self.tr("Select available algorithms to import."), self))
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def _import(self):
        for index in self.tableView.selectedIndexes():
            if index.column() == 0:
                # Use the assigned proxy model to map the index.
                index = self.tableView.model().mapToSource(index)
                algorithm = self.menu.algorithms[index.row()]
                if self.baseMenu.algorithmByIndex(algorithm.index):
                    freeIndices = [i for i in range(MaxAlgorithms) if self.menu.algorithmByIndex(i) is None]
                    algorithm.index = freeIndices[0]
                    QMessageBox.information(self,
                        self.tr("Relocating"),
                        QString("Moving algorithm <em>%1</em> from already used index %2 to free index %3.").arg(algorithm.name).arg(algorithm.index).arg(freeIndices[0]),
                    )
                self.algorithms.append(algorithm)
                for name in algorithm.cuts():
                    cut = self.menu.cutByName(name)
                    if cut not in self.cuts:
                        self.cuts.append(cut)
        self.accept()
