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
from tmEditor import Toolbox

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from collections import namedtuple
import sys, os

AlignLeft = Qt.AlignLeft | Qt.AlignVCenter
AlignRight = Qt.AlignRight | Qt.AlignVCenter

def fAlgorithm(expr):
    """Experimental HTML syntax highlighting for algorithm expressions."""
    for function in ('comb', 'dist', 'mass'):
        expr = expr.replace('{0}'.format(function), '<span style="color: blue; font-weight: bold;">{0}</span>'.format(function))
    for op in ('AND', 'OR', 'NOT'):
        expr = expr.replace(' {0} '.format(op), ' <span style="color: darkblue; font-weight: bold;">{0}</span> '.format(op))
    return expr

def fCut(value):
    return format(float(value), '+.3f')

def fThreshold(value):
    value = str(value).replace('p', '.') # Replace 'p' by comma.
    return "{0:.1f} GeV".format(float(value))

def fComparison(value):
    return str(value).strip('.')

def fBxOffset(value):
    return '0' if int(value) == 0 else format(int(value), '+d')

class Document(QWidget):
    """Document container widget used by MDI area."""

    def __init__(self, filename, parent = None):
        super(Document, self).__init__(parent)
        # Attributes
        self.setFilename(filename)
        self.setName(os.path.basename(filename))
        self.setModified(False)
        self.loadMenu(filename)
        # Layout
        self.setContentsMargins(0, 0, 0, 0)
        # Setup models
        self.menuModel = MenuModel(self.menu(), self)
        self.algorithmsModel = AlgorithmsModel(self.menu(), self)
        self.cutsModel = CutsModel(self.menu(), self)
        self.objectsModel = ObjectsModel(self.menu(), self)
        # Editor field
        self.editor = AlgorithmEditor("", self.menu())
        self.editor.setWindowModality(Qt.ApplicationModal)
        self.editor.setWindowFlags(self.editor.windowFlags() | Qt.Dialog)
        self.editor.hide()
        # Navigation tree
        self.navigationTreeWidget = QTreeWidget(self)
        self.navigationTreeWidget.headerItem().setHidden(True)
        self.navigationTreeWidget.setObjectName("navigationTreeWidget")
        self.navigationTreeWidget.setStyleSheet("#navigationTreeWidget { border: 0; background: #eee;}")
        self.menuItem = QTreeWidgetItem(self.navigationTreeWidget, ["Menu"])
        font = self.menuItem.font(0)
        font.setBold(True)
        self.menuItem.setFont(0, font)
        self.algorithmsItem = QTreeWidgetItem(self.menuItem, ["Algorithms"])
        self.cutsItem = QTreeWidgetItem(self.menuItem, ["Cuts"])
        self.objectsItem = QTreeWidgetItem(self.menuItem, ["Objects"])
        self.environmentItem = QTreeWidgetItem(self.navigationTreeWidget, ["Settings"])
        font = self.environmentItem.font(0)
        font.setBold(True)
        self.environmentItem.setFont(0, font)
        QTreeWidgetItem(self.environmentItem, ["Scales"])
        QTreeWidgetItem(self.environmentItem, ["External Signals"])
        self.navigationTreeWidget.expandAll()
        self.navigationTreeWidget.itemSelectionChanged.connect(self.updateViews)
        # Table view
        self.itemsTableView = QTableView(self)
        self.itemsTableView.setAlternatingRowColors(True)
        self.itemsTableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.itemsTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        delegate = HTMLDelegate()
        self.itemsTableView.setItemDelegate(delegate)
        # self.itemsTableView.setSortingEnabled(True) # TODO use sort-filter-proxy
        self.itemsTableView.setObjectName("itemsTableView")
        self.itemsTableView.setStyleSheet("#itemsTableView { border: 0; }")
        self.itemsTableView.doubleClicked.connect(self.editItem)
        horizontalHeader = self.itemsTableView.horizontalHeader()
        horizontalHeader.setResizeMode(QHeaderView.Stretch)
        horizontalHeader.setStretchLastSection(True)
        verticalHeader = self.itemsTableView.verticalHeader()
        verticalHeader.setResizeMode(QHeaderView.ResizeToContents)
        verticalHeader.setVisible(False)
        self.previewWidget = QTextEdit(self)
        self.previewWidget.setObjectName("previewWidget")
        self.previewWidget.setStyleSheet("""#previewWidget {
            border: 0;
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(203, 222, 238, 255), stop:1 rgba(233, 233, 233, 255));
        }""")
        # Splitters
        self.vsplitter = SlimSplitter(Qt.Horizontal, self)
        self.vsplitter.setObjectName("vsplitter")
        self.vsplitter.setStyleSheet("#vsplitter { border: 0; background: #888; }")
        self.vsplitter.addWidget(self.navigationTreeWidget)
        self.vsplitter.setOpaqueResize(False)
        self.hsplitter = SlimSplitter(Qt.Vertical, self)
        self.hsplitter.addWidget(self.itemsTableView)
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
        self._menu = Toolbox.L1MenuContainer(filename)

    def updateViews(self):
        item = self.navigationTreeWidget.selectedItems()
        if not len(item): return
        item = item[0]
        if item is self.menuItem:
            self.itemsTableView.setModel(self.menuModel)
        elif item is self.algorithmsItem:
            self.itemsTableView.setModel(self.algorithmsModel)
        elif item is self.cutsItem:
            self.itemsTableView.setModel(self.cutsModel)
        elif item is self.objectsItem:
            self.itemsTableView.setModel(self.objectsModel)
        else:
            self.itemsTableView.setModel(None)
        self.itemsTableView.resizeColumnsToContents()
        horizontalHeader = self.itemsTableView.horizontalHeader()
        horizontalHeader.setResizeMode(QHeaderView.Stretch)
        horizontalHeader.setStretchLastSection(True)

    def editItem(self, index):
        if self.itemsTableView.model() is self.algorithmsModel:
            if index.isValid():
                self.editor.setAlgorithm(self.menu().algorithms[index.row()]['expression'])
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

# From http://stackoverflow.com/questions/1956542/how-to-make-item-view-render-rich-html-text-in-qt
class HTMLDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        options = QStyleOptionViewItemV4(option)
        self.initStyleOption(options,index)
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
            return self.columnSpecs[column].alignment or QVariant()
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
