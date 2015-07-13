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

from tmEditor import Toolbox

from tmEditor import AlgorithmEditorDialog
from tmEditor import AlgorithmFormatter
from tmEditor import AlgorithmSyntaxHighlighter
from tmEditor import Menu
from tmEditor.Menu import Algorithm

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

    modified = pyqtSignal()

    def __init__(self, filename, parent = None):
        super(Document, self).__init__(parent)
        # Attributes
        self.loadMenu(filename)
        self.formatter = AlgorithmFormatter()
        # Layout
        self.setContentsMargins(0, 0, 0, 0)
        # Create table views.
        menuTableView = self.createProxyTableView("menuTableView", MenuModel(self.menu()))
        algorithmsTableView = self.createProxyTableView("algorithmsTableView", AlgorithmsModel(self.menu(), self))
        cutsTableView = self.createProxyTableView("cutsTableView", CutsModel(self.menu(), self))
        objectsTableView = self.createProxyTableView("objectsTableView", ObjectsModel(self.menu(), self))
        externalsTableView = self.createProxyTableView("externalsTableView", ExternalsModel(self.menu(), self))
        binsTableViews = {}
        for scale in self.menu().scales.bins.keys():
            binsTableViews[scale] = self.createProxyTableView("{scale}TableView".format(**locals()), BinsModel(self.menu(), scale, self))
        extSignalsTableView = self.createProxyTableView("externalsTableView", ExtSignalsModel(self.menu(), self))
        # Table view
        self.dataViewStack = QStackedWidget(self)
        ### self.dataViewStack.addWidget(QTextEdit(self))
        # Preview
        self.bottomWidget = BottomWidget(self)
        self.bottomWidget.addTriggered.connect(self.addItem)
        self.bottomWidget.editTriggered.connect(self.editItem)
        self.bottomWidget.removeTriggered.connect(self.removeItem)
        # Navigation tree
        self.navigationTreeWidget = QTreeWidget(self)
        self.navigationTreeWidget.headerItem().setHidden(True)
        self.navigationTreeWidget.setObjectName("navigationTreeWidget")
        self.navigationTreeWidget.setStyleSheet("#navigationTreeWidget { border: 0; background: #eee;}")
        # Add navigation items.
        self.menuItem = NavigationItem(self.navigationTreeWidget, "Menu", menuTableView, self.bottomWidget)
        self.algorithmsItem = NavigationItem(self.menuItem, "Algorithms", algorithmsTableView, self.bottomWidget)
        self.cutsItem = NavigationItem(self.menuItem, "Cuts", cutsTableView, self.bottomWidget)
        self.objectsItem = NavigationItem(self.menuItem, "Objects", objectsTableView, self.bottomWidget)
        self.externalsItem = NavigationItem(self.menuItem, "Externals", externalsTableView, self.bottomWidget)
        self.scalesItem = NavigationItem(self.navigationTreeWidget, "Scales", QLabel("Select a scale set...", self), self.bottomWidget)
        self.scalesTypeItem = {}
        for scale in self.menu().scales.bins.keys():
            self.scalesTypeItem[scale] = NavigationItem(self.scalesItem, scale, binsTableViews[scale], self.bottomWidget)
        self.extSignalsItem = NavigationItem(self.navigationTreeWidget, "External Signals", extSignalsTableView, self.bottomWidget)
        # Finsish navigation setup.
        self.navigationTreeWidget.expandItem(self.menuItem)
        self.navigationTreeWidget.itemSelectionChanged.connect(self.updateViews)
        self.navigationTreeWidget.setCurrentItem(self.menuItem)
        # Splitters
        self.vsplitter = SlimSplitter(Qt.Horizontal, self)
        self.vsplitter.setObjectName("vsplitter")
        self.vsplitter.setStyleSheet("#vsplitter { border: 0; background: #888; }")
        self.vsplitter.addWidget(self.navigationTreeWidget)
        self.vsplitter.setOpaqueResize(False)
        self.hsplitter = SlimSplitter(Qt.Vertical, self)
        self.hsplitter.addWidget(self.dataViewStack)
        self.hsplitter.addWidget(self.bottomWidget)
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

    def createProxyTableView(self, name, model):
        proxyModel = QSortFilterProxyModel(self)
        proxyModel.setSourceModel(model)
        tableView = TableView(self)
        tableView.setObjectName(name)
        tableView.setStyleSheet("#{name} {{ border: 0; }}".format(**locals()))
        tableView.setModel(proxyModel)
        tableView.doubleClicked.connect(self.editItem)
        tableView.selectionModel().selectionChanged.connect(self.updatePreview)
        return tableView

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
        """Load menu from filename, setup new document."""
        self.setModified(False)
        self.setFilename(filename)
        self.setName(os.path.basename(filename))
        self._menu = Menu()
        self._menu.loadXml(filename)

    def saveMenu(self, filename = None):
        """Save menu to filename."""
        filename = filename or self.filename()
        self._menu.saveXml(filename)
        self.setFilename(filename)
        self.setName(os.path.basename(filename))
        self.setModified(False)
        index, item = self.getSelection()
        item.view.update()

    def getSelection(self):
        items = self.navigationTreeWidget.selectedItems()
        if not len(items):
            return None, None
        item = items[0]
        index = item.view.currentMappedIndex()
        return index, item

    def getUnusedAlgorithmIndices(self):
        free = range(512)
        for algorithm in self.menu().algorithms:
            free.remove(int(algorithm.index))
        return free

    def updateViews(self):
        index, item = self.getSelection()
        if 0 > self.dataViewStack.indexOf(item.view):
            self.dataViewStack.addWidget(item.view)
            if hasattr(item.view, 'sortByColumn'):
                item.view.sortByColumn(0, Qt.AscendingOrder)
        self.dataViewStack.setCurrentWidget(item.view)
        self.updatePreview()

    def updatePreview(self):
        index, item = self.getSelection()
        # Generic preview...
        try:
            data = item.view.model().sourceModel().values[index.row()]
            item.preview.setText('<br/>'.join(["<strong>{0}:</strong> {1}".format(key, value) for key, value in data.items()]))
        except:
            item.preview.setText("")
        try:
            if item is self.algorithmsItem:
                item.preview.toolbar.show()
            elif item is self.cutsItem:
                item.preview.toolbar.show()
            else:
                item.preview.toolbar.hide()
        except:
            item.preview.setText("")
            item.preview.toolbar.hide()


    def addItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsItem:
            dialog = AlgorithmEditorDialog(self.menu(), self)
            dialog.setModal(True)
            dialog.setIndex(self.getUnusedAlgorithmIndices()[0])
            dialog.setName("L1_Unnamed")
            dialog.exec_()
            if dialog.result() == QDialog.Accepted:
                self.setModified(True)
                algorithm = self.menu().addAlgorithm(dialog.index(), dialog.name(), dialog.expression())
                item.view.model().setSourceModel(item.view.model().sourceModel())
                # REBUILD INDEX
                self.updatePreview()
                self.modified.emit()

    def editItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsItem:
            dialog = AlgorithmEditorDialog(self.menu(), self)
            dialog.setModal(True)
            dialog.setIndex(self.menu().algorithms[index.row()].index)
            dialog.setName(self.menu().algorithms[index.row()].name)
            dialog.setExpression(self.menu().algorithms[index.row()].expression)
            dialog.exec_()
            if dialog.result() == QDialog.Accepted:
                self.setModified(True)
                self.menu().algorithms[index.row()]['expression'] = dialog.expression()
                self.menu().algorithms[index.row()]['index'] = str(dialog.index())
                self.menu().algorithms[index.row()]['name'] = str(dialog.name())
                # REBUILD INDEX
                self.updatePreview()
                self.modified.emit()

    def copyItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsItem:
            algorithm = self.menu().algorithms[index.row()]
            dialog = AlgorithmEditorDialog(self.menu(), self)
            dialog.setModal(True)
            dialog.setIndex(self.getUnusedAlgorithmIndices()[0])
            dialog.setName(algorithm.name + "_copy")
            dialog.setExpression(algorithm.expression)
            dialog.exec_()
            if dialog.result() == QDialog.Accepted:
                self.setModified(True)
                self.menu().algorithms[index.row()]['expression'] = dialog.expression()
                self.menu().algorithms[index.row()]['index'] = str(dialog.index())
                self.menu().algorithms[index.row()]['name'] = str(dialog.name())
                # REBUILD INDEX
                self.updatePreview()
                self.modified.emit()

    def removeItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsItem:
            algorithm = self.menu().algorithms[index.row()]
            self.menu().algorithms.remove(algorithm)
            item.view.model().setSourceModel(item.view.model().sourceModel())
            # REBUILD INDEX
            self.updatePreview()
            self.modified.emit()
            self.setModified(True)
        elif item is self.cutsItem:
            cut = self.menu().cuts[index.row()]
            for algorithm in self.menu().algorithms:
                if cut.name in algorithm.cuts():
                    QMessageBox.warning(self,
                        "Cut is used",
                        "Cut {cut.name} is used by algorithm {algorithm.name}".format(**locals()),
                    )
                    return
            self.menu().cuts.remove(cut)
            item.view.model().setSourceModel(item.view.model().sourceModel())
            # REBUILD INDEX
            self.updatePreview()
            self.modified.emit()
            self.setModified(True)

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
    def __init__(self, parent, name, view, preview):
        super(NavigationItem, self).__init__(parent, [name])
        self.name = name
        self.view = view
        self.preview = preview
        if not isinstance(parent, NavigationItem):
            # Hilight root items in bold text.
            font = self.font(0)
            font.setBold(True)
            self.setFont(0, font)

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

# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------

class BottomWidget(QWidget):

    addTriggered = pyqtSignal()
    editTriggered = pyqtSignal()
    removeTriggered = pyqtSignal()

    def __init__(self, parent = None):
        super(BottomWidget, self).__init__(parent)
        self.toolbar = QWidget(self)
        self.toolbar.setAutoFillBackground(True)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        addButton = QPushButton(Toolbox.createIcon('actions', 'list-add'), "Add...", self)
        addButton.clicked.connect(self.onAdd)
        layout.addWidget(addButton)
        layout.addStretch(10)
        editButton = QPushButton(Toolbox.createIcon('apps', 'text-editor'), "Edit...", self)
        editButton.clicked.connect(self.onEdit)
        layout.addWidget(editButton)
        layout.addWidget(QPushButton(Toolbox.createIcon('actions', 'edit-copy'), "Copy...", self))
        removeBotton = QPushButton(Toolbox.createIcon('actions', 'list-remove'), "Delete", self)
        removeBotton.clicked.connect(self.onRemove)
        layout.addWidget(removeBotton)
        self.toolbar.setLayout(layout)
        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("BottomWidgetTextEdit")
        self.textEdit.setStyleSheet("""#BottomWidgetTextEdit {
            border: 0;
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(203, 222, 238, 255), stop:1 rgba(233, 233, 233, 255));
        }""")
        self.textEditHighlighter = AlgorithmSyntaxHighlighter(self.textEdit)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)
    def setText(self, message):
        self.textEdit.setText(message)
    def onAdd(self):
        self.addTriggered.emit()
    def onEdit(self):
        self.editTriggered.emit()
    def onRemove(self):
        self.removeTriggered.emit()

# ------------------------------------------------------------------------------
#  Models
# ------------------------------------------------------------------------------

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
            if spec.key not in self.values[row].keys():
                return QVariant()
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
        # self.addColumnSpec("ID", 'algorithm_id', int, AlignRight)

class CutsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(CutsModel, self).__init__(menu.cuts, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Object", 'object')
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
        self.addColumnSpec("Data", 'data')
        # self.addColumnSpec("ID", 'cut_id', int, AlignRight)

class ObjectsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ObjectsModel, self).__init__(menu.objects, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Threshold", 'threshold', fThreshold, AlignRight)
        self.addColumnSpec("Comparison", 'comparison_operator', fComparison, AlignRight)
        self.addColumnSpec("BX Offset", 'bx_offset', fBxOffset, AlignRight)
        # self.addColumnSpec("ID", 'object_id', int, AlignRight)

class ExternalsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ExternalsModel, self).__init__(menu.externals, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("BX Offset", 'bx_offset', fBxOffset, AlignRight)
        self.addColumnSpec("Comment", 'comment')
        self.addColumnSpec("Timestamp", 'datetime')
        # self.addColumnSpec("ID", 'requirement_id', int, AlignRight)
        # self.addColumnSpec("ID2", 'ext_signal_id', int, AlignRight)

class BinsModel(BaseTableModel):

    def __init__(self, menu, name, parent = None):
        super(BinsModel, self).__init__(menu.scales.bins[name])
        self.name = name
        self.addColumnSpec("Number", 'number', int, AlignRight)
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
        # self.addColumnSpec("ID", 'scale_id', int, AlignRight)

class ExtSignalsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ExtSignalsModel, self).__init__(menu.extSignals.extSignals, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Label", 'label')
        self.addColumnSpec("System", 'system')
        self.addColumnSpec("Cable", 'cable')
        self.addColumnSpec("Channel", 'channel')
        self.addColumnSpec("Description", 'description')
        # self.addColumnSpec("ID", 'ext_signal_id', int, AlignRight)
