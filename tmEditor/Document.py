# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Document widget.
"""

from tmEditor import AlgorithmEditor
from tmEditor import Toolbox

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys, os

class Document(QWidget):
    """Document container widget used by MDI area."""

    def __init__(self, filename, parent = None):
        super(Document, self).__init__(parent)
        self.setName(os.path.basename(filename))
        self.setModified(False)
        self.setContentsMargins(0, 0, 0, 0)
        # Menu setup
        self.menu = Toolbox.Menu(filename)
        self.algorithmsModel = AlgorithmsModel(self.menu)
        self.cutsModel = CutsModel(self.menu)
        self.objectsModel = ObjectsModel(self.menu)
        # Editor field
        self.editor = AlgorithmEditor("", self.menu)
        self.editor.setWindowModality(Qt.ApplicationModal)
        self.editor.setWindowFlags(self.editor.windowFlags() | Qt.Dialog)
        self.editor.hide()
        # Navigation tree
        self.navigationTreeWidget = QTreeWidget(self)
        self.navigationTreeWidget.setObjectName("navigationTreeWidget")
        self.navigationTreeWidget.setStyleSheet("#navigationTreeWidget { background: #eee; }")
        item = QTreeWidgetItem(self.navigationTreeWidget,[self.name()])
        self.algorithmsItem = QTreeWidgetItem(item, ["Algorithms"])
        self.cutsItem = QTreeWidgetItem(item, ["Cuts"])
        self.objectsItem = QTreeWidgetItem(item, ["Objects"])
        self.navigationTreeWidget.expandAll()
        self.navigationTreeWidget.itemSelectionChanged.connect(self.updateViews)
        # Table view
        self.itemsTableView = QTableView(self)
        self.itemsTableView.doubleClicked.connect(self.editItem)
        horizontalHeader = self.itemsTableView.horizontalHeader()
        horizontalHeader.setResizeMode(QHeaderView.Stretch)
        horizontalHeader.setStretchLastSection(True)
        verticalHeader = self.itemsTableView.verticalHeader()
        verticalHeader.setResizeMode(QHeaderView.ResizeToContents)
        self.setStyleSheet("border: 0;")
        self.itemPreview = QTextEdit(self)
        self.itemPreview.setObjectName("P")
        self.itemPreview.setStyleSheet("#P { background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(205, 205, 255, 255), stop:1 rgba(255, 255, 255, 255));; }")
        # Splitters
        self.vsplitter = SlimSplitter(Qt.Horizontal, self)
        self.vsplitter.setObjectName("A")
        self.vsplitter.setStyleSheet("#A { background: #888; }")
        self.vsplitter.addWidget(self.navigationTreeWidget)
        self.vsplitter.setOpaqueResize(False)
        self.hsplitter = SlimSplitter(Qt.Vertical, self)
        self.hsplitter.addWidget(self.itemsTableView)
        self.hsplitter.addWidget(self.itemPreview)
        self.vsplitter.addWidget(self.hsplitter)
        self.vsplitter.setStretchFactor(0, 0)
        self.vsplitter.setStretchFactor(1, 1)
        self.vsplitter.setSizes([200, 600])
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.vsplitter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def name(self):
        return self._name

    def setName(self, name):
        self._name = str(name)

    def isModified(self):
        return self._isModified

    def setModified(self, modified):
        self._isModified = bool(modified)

    def updateViews(self):
        item = self.navigationTreeWidget.selectedItems()
        if not len(item): return
        item = item[0]
        if item is self.algorithmsItem:
            self.itemsTableView.setModel(self.algorithmsModel)
        elif item is self.cutsItem:
            self.itemsTableView.setModel(self.cutsModel)
        elif item is self.objectsItem:
            self.itemsTableView.setModel(self.objectsModel)
        self.itemsTableView.resizeColumnsToContents()
        horizontalHeader = self.itemsTableView.horizontalHeader()
        horizontalHeader.setResizeMode(QHeaderView.Stretch)
        horizontalHeader.setStretchLastSection(True)

    def editItem(self, index):
        if self.itemsTableView.model() is self.algorithmsModel:
            if index.isValid():
                self.editor.setAlgorithm(self.menu.algorithms[index.row()]['expression'])
                self.editor.reloadLibrary()
                self.editor.show()

class SlimSplitter(QSplitter):
    """Slim splitter with a decent narrow splitter handle."""

    def __init__(self, orientation, parent = None):
        super(SlimSplitter, self).__init__(orientation, parent)
        self.setHandleWidth(1)
        self.setContentsMargins(0, 0, 0, 0)

    def createHandle(self):
        return SlimSplitterHandle(self.orientation(), self)

class SlimSplitterHandle(QSplitterHandle):
    """Custom splitter handle for the slim splitter."""

    def __init__(self, orientation, parent = None):
        super(SlimSplitterHandle, self).__init__(orientation, parent)

    def paintEvent(self, event):
        pass

class AlgorithmsModel(QAbstractTableModel):
    ColumnTitles = (
        "Name",
        "Expression",
    )
    def __init__(self, menu, parent = None):
        super(AlgorithmsModel, self).__init__(parent)
        self.menu = menu
    def rowCount(self, parent):
        return len(self.menu.algorithms)
    def columnCount(self, parent):
        return len(self.ColumnTitles)
    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.isValid():
                if index.column() == 0:
                    return self.menu.algorithms[index.row()]['name']
                if index.column() == 1:
                    return self.menu.algorithms[index.row()]['expression']
        return QVariant()
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.ColumnTitles[section]
        return QVariant()

class CutsModel(QAbstractTableModel):
    ColumnTitles = (
        "Name",
        "Type",
        "Object",
        "Min",
        "Max",
        "Data",
    )
    def __init__(self, menu, parent = None):
        super(CutsModel, self).__init__(parent)
        self.menu = menu
    def rowCount(self, parent):
        return len(self.menu.cuts)
    def columnCount(self, parent):
        return len(self.ColumnTitles)
    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.isValid():
                if index.column() == 0:
                    return self.menu.cuts[index.row()]['name']
                if index.column() == 1:
                    return self.menu.cuts[index.row()]['type']
                if index.column() == 2:
                    return self.menu.cuts[index.row()]['object']
                if index.column() == 3:
                    return format(float(self.menu.cuts[index.row()]['minimum']), '+.3f')
                if index.column() == 4:
                    return format(float(self.menu.cuts[index.row()]['maximum']), '+.3f')
                if index.column() == 5:
                    return self.menu.cuts[index.row()]['data']
        return QVariant()
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.ColumnTitles[section]
        return QVariant()

class ObjectsModel(QAbstractTableModel):
    ColumnTitles = (
        "Name",
        "Type",
        "Threshold",
        "Comp",
        "BX Offset",
    )
    def __init__(self, menu, parent = None):
        super(ObjectsModel, self).__init__(parent)
        self.menu = menu
    def rowCount(self, parent):
        return len(self.menu.objects)
    def columnCount(self, parent):
        return len(self.ColumnTitles)
    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.isValid():
                if index.column() == 0:
                    return self.menu.objects[index.row()]['name']
                if index.column() == 1:
                    return self.menu.objects[index.row()]['type']
                if index.column() == 2:
                    return format(float(self.menu.objects[index.row()]['threshold']), '.1f')
                if index.column() == 3:
                    return self.menu.objects[index.row()]['comparison_operator']
                if index.column() == 4:
                    return format(int(self.menu.objects[index.row()]['bx_offset']), '+d')
        return QVariant()
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.ColumnTitles[section]
        return QVariant()
