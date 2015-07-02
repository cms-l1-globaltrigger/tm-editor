# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

# TODO clean up this mess!

"""Document widget.
"""

from tmEditor import AlgorithmEditor
from tmEditor import AlgorithmFormatter
from tmEditor.AlgorithmEditor import SyntaxHighlighter
from tmEditor import Menu

from tmEditor.Toolbox import (
    fAlgorithm,
    fCut,
    fThreshold,
    fComparison,
    fBxOffset,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from collections import namedtuple
import sys, os

AlignLeft = Qt.AlignLeft | Qt.AlignVCenter
AlignRight = Qt.AlignRight | Qt.AlignVCenter

# ------------------------------------------------------------------------------
#  Document widget
# ------------------------------------------------------------------------------

class Document(QWidget):
    """Document container widget used by MDI area."""

    def __init__(self, filename, parent = None):
        super(Document, self).__init__(parent)
        # Attributes
        self.setFilename(filename)
        self.setName(os.path.basename(filename))
        self.setModified(False)
        self.loadMenu(filename)
        self.formatter = AlgorithmFormatter()
        # Layout
        self.setContentsMargins(0, 0, 0, 0)
        # Setup models
        self.menuModel = MenuModel(self.menu(), self)
        self.algorithmsModel = AlgorithmsModel(self.menu(), self)
        self.cutsModel = CutsModel(self.menu(), self)
        self.objectsModel = ObjectsModel(self.menu(), self)
        self.binsModel = {} #BinsModel(self.menu(), self)
        # Editor window (persistent instance)
        self.editorWindow = AlgorithmEditor("", self.menu())
        self.editorWindow.setWindowModality(Qt.ApplicationModal)
        self.editorWindow.setWindowFlags(self.editorWindow.windowFlags() | Qt.Dialog)
        self.editorWindow.hide()
        # Creating a proxy model for sort function
        self.proxyModel = QSortFilterProxyModel(self)
        # Table view
        self.tableView = TableView(self)
        self.tableView.setObjectName("tableView")
        self.tableView.setStyleSheet("#tableView { border: 0; }")
        self.tableView.setModel(self.proxyModel)
        self.tableView.doubleClicked.connect(self.editItem)
        # Preview
        self.previewWidget = QTextEdit(self)
        self.previewWidget.setReadOnly(True)
        self.previewWidgetHighlighter = SyntaxHighlighter(self.previewWidget)
        self.previewWidget.setObjectName("previewWidget")
        self.previewWidget.setStyleSheet("""#previewWidget {
            border: 0;
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(203, 222, 238, 255), stop:1 rgba(233, 233, 233, 255));
        }""")
        # Navigation tree
        self.navigationTreeWidget = QTreeWidget(self)
        self.navigationTreeWidget.headerItem().setHidden(True)
        self.navigationTreeWidget.setObjectName("navigationTreeWidget")
        self.navigationTreeWidget.setStyleSheet("#navigationTreeWidget { border: 0; background: #eee;}")
        self.menuItem = NavigationItem(self.navigationTreeWidget, "Menu", QPushButton("push", self), QTextEdit(self))
        self.menuItem.previewWidget.setPlainText("so far...")
        font = self.menuItem.font(0)
        font.setBold(True)
        self.menuItem.setFont(0, font)
        self.algorithmsItem = NavigationItem(self.menuItem, "Algorithms", self.tableView, self.previewWidget)
        self.cutsItem = NavigationItem(self.menuItem, "Cuts", self.tableView, self.previewWidget)
        self.objectsItem = NavigationItem(self.menuItem, "Objects", self.tableView, self.previewWidget)
        self.scalesItem = NavigationItem(self.navigationTreeWidget, "Scales", self.tableView, self.previewWidget)
        self.scalesTypeItem = {}
        for name in self.menu().scales.bins.keys():
            self.scalesTypeItem[name] = NavigationItem(self.scalesItem, name, self.tableView, self.previewWidget)
            self.binsModel[name] = BinsModel(self.menu(), name, self)
        self.extSignalsItem = NavigationItem(self.navigationTreeWidget, "External Signals", self.tableView, self.previewWidget)
        font = self.scalesItem.font(0)
        font.setBold(True)
        self.scalesItem.setFont(0, font)
        font = self.extSignalsItem.font(0)
        font.setBold(True)
        self.extSignalsItem.setFont(0, font)
        self.navigationTreeWidget.expandAll()
        self.navigationTreeWidget.itemSelectionChanged.connect(self.updateViews)
        # Splitters
        self.vsplitter = SlimSplitter(Qt.Horizontal, self)
        self.vsplitter.setObjectName("vsplitter")
        self.vsplitter.setStyleSheet("#vsplitter { border: 0; background: #888; }")
        self.vsplitter.addWidget(self.navigationTreeWidget)
        self.vsplitter.setOpaqueResize(False)
        self.hsplitter = SlimSplitter(Qt.Vertical, self)
        self.hsplitter.addWidget(self.tableView)
        self.hsplitter.addWidget(self.previewWidget)
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

    def filename(self):
        return self._filename

    def setFilename(self, filename):
        self._filename = os.path.abspath(filename)

    def name(self):
        return self._name

    def setName(self, name):
        self._name = str(name)

    def isModified(self):
        return self._isModified

    def setModified(self, modified):
        self._isModified = bool(modified)

    def menu(self):
        return self._menu

    def loadMenu(self, filename):
        self._menu = Menu(filename)

    def updateViews(self):
        item = self.navigationTreeWidget.selectedItems()
        if not len(item): return
        item = item[0]
        if item is self.menuItem:
            self.tableView.showModel(self.menuModel)
        elif item is self.algorithmsItem:
            self.tableView.showModel(self.algorithmsModel)
        elif item is self.cutsItem:
            self.tableView.showModel(self.cutsModel)
        elif item is self.objectsItem:
            self.tableView.showModel(self.objectsModel)
        elif item in self.scalesTypeItem.values():
            if item.name in self.scalesTypeItem.keys():
                self.tableView.showModel(self.binsModel[item.name])
        else:
            self.tableView.showModel(None)

    def updatePreview(self):
        index = self.tableView.currentMappedIndex()
        item = self.navigationTreeWidget.selectedItems()
        if not len(item):
            return
        item = item[0]
        if item is self.algorithmsItem:
            self.previewWidget.setPlainText(self.formatter.humanize(self.menu().algorithms[index.row()]['expression']))
        elif item is self.cutsItem:
            self.previewWidget.setPlainText(self.menu().cuts[index.row()]['name'])
        else:
            self.previewWidget.setPlainText("")

    def editItem(self, index):
        model = self.tableView.model()
        index = model.mapToSource(index)
        if not index.isValid():
            return
        if model.sourceModel() is self.algorithmsModel:
            self.editorWindow.setAlgorithm(self.menu().algorithms[index.row()]['expression'])
            self.editorWindow.reloadLibrary()
            self.editorWindow.show()

# ------------------------------------------------------------------------------
#  Splitter and custom handle
# ------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------
#  Navigation tree item
# ------------------------------------------------------------------------------

class NavigationItem(QTreeWidgetItem):
    def __init__(self, parent, name, dataWidget, previewWidget):
        super(NavigationItem, self).__init__(parent, [name])
        self.name = name
        self.dataWidget = dataWidget
        self.previewWidget = previewWidget

# ------------------------------------------------------------------------------
#  Common table view widget
# ------------------------------------------------------------------------------

class TableView(QTableView):
    """Common sortable table view wiget."""

    def __init__(self, parent = None):
        """@param parent optional parent widget.
        """
        super(TableView, self).__init__(parent)
        # Setup table view.
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        # Setup horizontal column appearance.
        horizontalHeader = self.horizontalHeader()
        horizontalHeader.setHighlightSections(False)
        horizontalHeader.setResizeMode(QHeaderView.Interactive)
        horizontalHeader.setStretchLastSection(True)
        # Setup vertical row appearance.
        verticalHeader = self.verticalHeader()
        verticalHeader.setResizeMode(QHeaderView.Fixed)
        verticalHeader.setDefaultSectionSize(20)
        verticalHeader.hide()
        self.setSortingEnabled(True)
        #
        self.horizontalSectionWidths = {}

    def currentMappedIndex(self):
        """@returns current selected proxy mapped index, else None."""
        # Get the current selected table view index.
        index = self.selectedIndexes()
        if index:
            # Use the assigned proxy model to map the index.
            return self.model().mapToSource(index[0])

    def getColumnWidths(self):
        horizontalHeader = self.horizontalHeader()
        count = horizontalHeader.count()
        return [horizontalHeader.sectionSize(i) for i in range(count)]

    def showModel(self, model):
        if self.model() and self.model().sourceModel():
            self.horizontalSectionWidths[self.model().sourceModel()] = self.getColumnWidths()
        self.model().setSourceModel(model)
        if model not in self.horizontalSectionWidths.keys():
            self.resizeColumnsToContents()
            self.horizontalSectionWidths[model] = self.getColumnWidths()
            self.sortByColumn(0)
        else:
            horizontalHeader = self.horizontalHeader()
            for i, width in enumerate(self.horizontalSectionWidths[model]):
                horizontalHeader.resizeSection(i, width)

# From http://stackoverflow.com/questions/1956542/how-to-make-item-view-render-rich-html-text-in-qt
class HTMLDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        options = QStyleOptionViewItemV4(option)
        self.initStyleOption(options, index)
        style = QApplication.style() if options.widget is None else options.widget.style()
        doc = QTextDocument()
        doc.setHtml(options.text)
        options.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, options, painter);
        ctx = QAbstractTextDocumentLayout.PaintContext()
        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItemV4(option)
        self.initStyleOption(options, index)
        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        return QSize(doc.idealWidth(), doc.size().height())

class BaseTableModel(QAbstractTableModel):
    """Abstract table model class to be inherited to display table data."""

    ColumnSpec = namedtuple('ColumnSpec', 'title, key, format, alignment')

    def __init__(self, values, parent = None):
        super(BaseTableModel, self).__init__(parent)
        self.values = values
        self.columnSpecs = []

    def addColumnSpec(self, title, key, format = str, alignment = AlignLeft):
        spec = self.ColumnSpec(title, key, format, alignment)
        self.columnSpecs.append(spec)
        return spec

    def rowCount(self, parent):
        return len(self.values)

    def columnCount(self, parent):
        return len(self.columnSpecs)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        row, column = index.row(), index.column()
        if role == Qt.DisplayRole:
            spec = self.columnSpecs[column]
            return spec.format(self.values[row][spec.key])
        if role == Qt.TextAlignmentRole:
            return self.columnSpecs[column].alignment
        return QVariant()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.columnSpecs[section].title
        return QVariant()

class MenuModel(QAbstractTableModel):

    def __init__(self, menu, parent = None):
        super(MenuModel, self).__init__(parent)
        self.menu = menu

    def rowCount(self, parent):
        return len(self.menu.menu)

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        row, column = index.row(), index.column()
        if role == Qt.DisplayRole:
            return self.menu.menu.items()[row][column]
        return QVariant()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return ("Key", "Value")[section]
        return QVariant()

class AlgorithmsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(AlgorithmsModel, self).__init__(menu.algorithms, parent)
        self.addColumnSpec("Index", 'index', int, AlignRight)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Expression", 'expression', fAlgorithm)

class CutsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(CutsModel, self).__init__(menu.cuts, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Object", 'object')
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
        self.addColumnSpec("Data", 'data')

class ObjectsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ObjectsModel, self).__init__(menu.objects, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Threshold", 'threshold', fThreshold, AlignRight)
        self.addColumnSpec("Comparison", 'comparison_operator', fComparison, AlignRight)
        self.addColumnSpec("BX Offset", 'bx_offset', fBxOffset, AlignRight)

class BinsModel(BaseTableModel):

    def __init__(self, menu, type_, parent = None):
        super(BinsModel, self).__init__(menu.scales.bins[type_])
        self.type_ = type_
        self.addColumnSpec("Number", 'number', int, AlignRight)
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
