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

from tmEditor import CutEditorDialog
from tmEditor import AlgorithmEditorDialog
from tmEditor import AlgorithmFormatter
from tmEditor import AlgorithmSyntaxHighlighter
from tmEditor import Menu
from tmEditor.Menu import Algorithm, Object, toObject

from tmEditor.Toolbox import (
    fAlgorithm,
    fCut,
    fHex,
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
AlignCenter = Qt.AlignCenter | Qt.AlignVCenter

MaxAlgorithms = 512

# ------------------------------------------------------------------------------
#  Document widget
# ------------------------------------------------------------------------------

class Document(QWidget):
    """Document container widget used by MDI area."""

    modified = pyqtSignal()
    """This signal is emitted whenever the content of the document changes."""

    def __init__(self, filename, parent = None):
        super(Document, self).__init__(parent)
        # Attributes
        self.loadMenu(filename)
        self.formatter = AlgorithmFormatter()
        # Layout
        self.setContentsMargins(0, 0, 0, 0)
        # Create table views.
        menuTableView = self.createProxyTableView("menuTableView", MenuModel(self.menu(), self))
        algorithmsTableView = self.createProxyTableView("algorithmsTableView", AlgorithmsModel(self.menu(), self))
        algorithmsTableView.resizeColumnsToContents()
        cutsTableView = self.createProxyTableView("cutsTableView", CutsModel(self.menu(), self))
        cutsTableView.resizeColumnsToContents()
        objectsTableView = self.createProxyTableView("objectsTableView", ObjectsModel(self.menu(), self))
        objectsTableView.resizeColumnsToContents()
        externalsTableView = self.createProxyTableView("externalsTableView", ExternalsModel(self.menu(), self))
        externalsTableView.resizeColumnsToContents()
        binsTableViews = {}
        for scale in self.menu().scales.bins.keys():
            binsTableViews[scale] = self.createProxyTableView("{scale}TableView".format(**locals()), BinsModel(self.menu(), scale, self))
        extSignalsTableView = self.createProxyTableView("externalsTableView", ExtSignalsModel(self.menu(), self))
        # Table view
        self.dataViewStack = QStackedWidget(self)
        ### self.dataViewStack.addWidget(QTextEdit(self))
        #
        menuView = QWidget(self)
        menuView.menu = self.menu()
        menuView.nameLineEdit = QLineEdit(self)
        menuView.commentTextEdit = QPlainTextEdit(self)
        menuView.commentTextEdit.setMaximumHeight(50)
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(self.tr("Name:"), self))
        vbox.addWidget(menuView.nameLineEdit)
        vbox.addWidget(QLabel(self.tr("Comment:"), self))
        vbox.addWidget(menuView.commentTextEdit)
        vbox.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        menuView.setLayout(vbox)
        menuView.setAutoFillBackground(True)
        #
        # Preview
        self.bottomWidget = BottomWidget(self)
        self.bottomWidget.addTriggered.connect(self.addItem)
        self.bottomWidget.editTriggered.connect(self.editItem)
        self.bottomWidget.copyTriggered.connect(self.copyItem)
        self.bottomWidget.removeTriggered.connect(self.removeItem)
        # Navigation tree
        self.navigationTreeWidget = QTreeWidget(self)
        self.navigationTreeWidget.headerItem().setHidden(True)
        self.navigationTreeWidget.setObjectName("navigationTreeWidget")
        self.navigationTreeWidget.setStyleSheet("#navigationTreeWidget { border: 0; background: #eee;}")
        # Add navigation items.
        self.menuItem = NavigationItem(self.navigationTreeWidget, "Menu", menuView, self.bottomWidget)
        self.algorithmsItem = NavigationItem(self.menuItem, "Algorithms", algorithmsTableView, self.bottomWidget)
        self.cutsItem = NavigationItem(self.menuItem, "Cuts", cutsTableView, self.bottomWidget)
        self.objectsItem = NavigationItem(self.menuItem, "Objects", objectsTableView, self.bottomWidget)
        self.externalsItem = NavigationItem(self.menuItem, "Externals", externalsTableView, self.bottomWidget)
        label = QLabel("Select a scale set...", self)
        label.setAutoFillBackground(True)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scalesItem = NavigationItem(self.navigationTreeWidget, "Scales", label, self.bottomWidget)
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
        #
        self.menuItem.view.nameLineEdit.setText(self.menu().menu['name'])
        self.menuItem.view.commentTextEdit.setPlainText(self.menu().menu['comment'] if 'comment' in self.menu().menu else '')

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

    def addPage(self, name, page, preview, parent):
        item = QTreeWidgetItem(self)
        if parent is self.navigationTreeWidget:
            # Hilight root items in bold text.
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        item.page = page
        item.preview = preview
        return item

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
        self._menu.menu['name'] = str(self.menuItem.view.nameLineEdit.text())
        self._menu.menu['comment'] = str(self.menuItem.view.commentTextEdit.toPlainText())
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
        if isinstance(item.view, QTableView):
            index = item.view.currentMappedIndex()
            return index, item
        return None, item

    def getUnusedAlgorithmIndices(self):
        free = [i for i in range(512)]
        for algorithm in self.menu().algorithms:
            if int(algorithm.index) in free:
                free.remove(int(algorithm.index))
        return free

    def updateViews(self):
        index, item = self.getSelection()
        try:
            if 0 > self.dataViewStack.indexOf(item.view):
                self.dataViewStack.addWidget(item.view)
                if hasattr(item.view, 'sortByColumn'):
                    item.view.sortByColumn(0, Qt.AscendingOrder)
            self.dataViewStack.setCurrentWidget(item.view)
            self.updatePreview()
        except:
            pass

    def updatePreview(self):
        index, item = self.getSelection()
        # Generic preview...
        try:
            data = dict([(key, value) for key, value in item.view.model().sourceModel().values[index.row()].items()]) # Local copy
            text = []
            if item is self.algorithmsItem:
                text.append("<h2>{name} ({index})</h2>")
                text.append("<p><strong>Expression:</strong></p><p><code>{expression}</code></p>")
            elif item is self.cutsItem:
                data['maximum'], data['minimum'] = fCut(data['maximum']), fCut(data['minimum'])
                text.append("<h2>{name}</h2>")
                text.append("<p><strong>Type:</strong> {object}</p>")
                if data['data']:
                    fdata = []
                    typename = "{0}-{1}".format(data['object'], data['type'])
                    data_ = filter(lambda entry: entry['name'] == typename, Toolbox.Settings['cuts'])[0]['data']
                    for n in data['data'].split(','):
                        fdata.append("{1} ({0})".format(int(n), data_[n.strip()]))
                    fdata = ', '.join(fdata)
                    text.append("<p><strong>Data:</strong> {translation}</p>".format(translation = fdata))
                else:
                    text.append("<p><strong>Minimum:</strong> {minimum}</p>")
                    text.append("<p><strong>Maximum:</strong> {maximum}</p>")
            elif item is self.objectsItem:
                data['threshold'] = fThreshold(str(data['threshold']))
                data['bx_offset'] = fBxOffset(data['bx_offset'])
                text.append("<h2>{name}</h2>")
                text.append("<p><strong>Type:</strong> {type}</p>")
                text.append("<p><strong>Threshold:</strong> {threshold}</p>")
                text.append("<p><strong>BX offset:</strong> {bx_offset}</p>")
            elif item is self.externalsItem:
                data['bx_offset'] = fBxOffset(data['bx_offset'])
                text.append("<h2>{name}</h2>")
                text.append("<p><strong>BX offset:</strong> {bx_offset}</p>")
            elif item in self.scalesTypeItem.values():
                data['name'] = item.name
                text.append("<h2>Scale {name}</h2>")
                text.append("<p><strong>Number:</strong> {number}</p>")
                data['maximum'], data['minimum'] = fCut(data['maximum']), fCut(data['minimum'])
                text.append("<p><strong>Minimum:</strong> {minimum}</p>")
                text.append("<p><strong>Maximum:</strong> {maximum}</p>")
            if 'comment' in data.keys():
                text.append("<p><strong>Comment:</strong></p><p><code>{comment}</code></p>")
            item.preview.setText(''.join(text).format(**data))
            item.preview.setButtonsEnabled(True)
        except AttributeError, m:
            item.preview.setText("<img style=\"float:left;\" src=\":icons/tm-editor.svg\"/><h1 style=\"margin-left:120px;\">Trigger Menu Editor</h1><p style=\"margin-left:120px;\"><em>Editing Level-1 Global Trigger Menus with ease</em></p>")
            item.preview.setButtonsEnabled(False)
        try:
            item.preview.notice.hide()
            if item is self.algorithmsItem:
                item.preview.toolbar.show()
            elif item is self.cutsItem:
                item.preview.toolbar.show()
            elif item is self.objectsItem:
                item.preview.toolbar.hide()
                item.preview.notice.setText(self.tr("<strong>Note:</strong> new objects are created directly in the algorithm editor."))
                item.preview.notice.show()
            else:
                item.preview.toolbar.hide()
        except:
            item.preview.setText("")
            item.preview.toolbar.hide()

    def addItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsItem:
            self.addAlgorithm(index, item)
        elif item is self.cutsItem:
            self.addCut(index, item)

    def addAlgorithm(self, index, item):
        dialog = AlgorithmEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.setIndex(self.getUnusedAlgorithmIndices()[0])
        dialog.setName("L1_Unnamed")
        dialog.editor.setModified(False)
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.setModified(True)
        algorithm = Algorithm()
        dialog.updateAlgorithm(algorithm)
        self.menu().addAlgorithm(**algorithm)
        item.view.model().setSourceModel(item.view.model().sourceModel())
        # REBUILD INDEX
        self.updatePreview()
        self.modified.emit()
        self.objectsItem.view.model().setSourceModel(self.objectsItem.view.model().sourceModel())
        for name in algorithm.cuts():
            if not filter(lambda item: item.name == name, self.menu().cuts):
                raise RuntimeError("NO SUCH CUT AVAILABLE")

    def addCut(self, index, item):
        dialog = CutEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.updateEntries()
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.setModified(True)
        self.menu().addCut(name=dialog.name(),
            object=dialog.object(),
            type=dialog.type(),
            minimum=dialog.minimum() or '',
            maximum=dialog.maximum() or '',
            data=dialog.data() or '',
            comment=dialog.comment())
        self.cutsItem.view.model().setSourceModel(self.cutsItem.view.model().sourceModel())

    def editItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsItem:
            self.editAlgorithm(index, item)
        elif item is self.cutsItem:
            self.editCut(index, item)
        self.updatePreview()

    def editAlgorithm(self, index, item):
        algorithm = self.menu().algorithms[index.row()]
        dialog = AlgorithmEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.loadAlgorithm(algorithm)
        dialog.editor.setModified(False)
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.setModified(True)
        dialog.updateAlgorithm(algorithm)
        # REBUILD INDEX
        self.updatePreview()
        self.modified.emit()
        self.menu().updateAlgorithm(algorithm)
        self.objectsItem.view.model().setSourceModel(self.objectsItem.view.model().sourceModel())
        for name in algorithm.cuts():
            if not filter(lambda item: item.name == name, self.menu().cuts):
                raise RuntimeError("NO SUCH CUT AVAILABLE")

    def editCut(self, index, item):
        cut = self.menu().cuts[index.row()]
        dialog = CutEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.typeComboBox.setEnabled(False)
        dialog.loadCut(cut)
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.setModified(True)
        dialog.updateCut(cut)
        self.cutsItem.view.model().setSourceModel(self.cutsItem.view.model().sourceModel())

    def copyItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsItem:
            self.copyAlgorithm(index, item)
        if item is self.cutsItem:
            self.copyCut(index, item)

    def copyAlgorithm(self, index, item):
        algorithm = Algorithm(**self.menu().algorithms[index.row()])
        dialog = AlgorithmEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.setIndex(self.getUnusedAlgorithmIndices()[0])
        dialog.setName(algorithm.name + "_copy")
        dialog.setExpression(algorithm.expression)
        dialog.editor.setModified(False)
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.setModified(True)
        algorithm['expression'] = dialog.expression()
        algorithm['index'] = str(dialog.index())
        algorithm['name'] = str(dialog.name())
        self.menu().algorithms.append(algorithm)
        item.view.model().setSourceModel(item.view.model().sourceModel())
        # REBUILD INDEX
        self.updatePreview()
        self.modified.emit()
        for name in algorithm.objects():
            if not filter(lambda item: item.name == name, self.menu().objects):
                self.menu().addObject(**toObject(name))
        self.objectsItem.view.model().setSourceModel(self.objectsItem.view.model().sourceModel())
        for name in algorithm.cuts():
            if not filter(lambda item: item.name == name, self.menu().cuts):
                raise RuntimeError("NO SUCH CUT AVAILABLE")
        for name in algorithm.externals():
            if not filter(lambda item: item.name == name, self.menu().externals):
                raise RuntimeError("NO SUCH CUT AVAILABLE")

    def copyCut(self, index, item):
        dialog = CutEditorDialog(self.menu(), self)
        dialog.setModal(True)
        cut = self.menu().cuts[index.row()]
        dialog.loadCut(cut)
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.setModified(True)
        self.menu().addCut(name=dialog.name(),
            object=dialog.object(),
            type=dialog.type(),
            minimum=dialog.minimum() or '',
            maximum=dialog.maximum() or '',
            data=dialog.data() or '',
            comment=dialog.comment())
        self.cutsItem.view.model().setSourceModel(self.cutsItem.view.model().sourceModel())

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
    copyTriggered = pyqtSignal()
    removeTriggered = pyqtSignal()

    def __init__(self, parent = None):
        super(BottomWidget, self).__init__(parent)
        self.toolbar = QWidget(self)
        self.toolbar.setAutoFillBackground(True)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.addButton = QPushButton(Toolbox.createIcon('actions', 'list-add'), "Add...", self)
        self.addButton.clicked.connect(self.onAdd)
        layout.addWidget(self.addButton)
        layout.addStretch(10)
        self.editButton = QPushButton(Toolbox.createIcon('apps', 'text-editor'), "Edit...", self)
        self.editButton.clicked.connect(self.onEdit)
        layout.addWidget(self.editButton)
        self.copyButton = QPushButton(Toolbox.createIcon('actions', 'edit-copy'), "Copy...", self)
        self.copyButton.clicked.connect(self.onCopy)
        layout.addWidget(self.copyButton)
        self.removeBotton = QPushButton(Toolbox.createIcon('actions', 'list-remove'), "Delete", self)
        self.removeBotton.clicked.connect(self.onRemove)
        layout.addWidget(self.removeBotton)
        self.toolbar.setLayout(layout)
        self.notice = QLabel(self)
        self.notice.hide()
        self.notice.setAutoFillBackground(True)
        self.notice.setStyleSheet("padding:10px;")
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
        layout.addWidget(self.notice)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)
    def setButtonsEnabled(self, enabled):
        self.editButton.setEnabled(enabled)
        self.copyButton.setEnabled(enabled)
        self.removeBotton.setEnabled(enabled)
    def setText(self, message):
        self.textEdit.setText(message)
    def onAdd(self):
        self.addTriggered.emit()
    def onEdit(self):
        self.editTriggered.emit()
    def onCopy(self):
        self.copyTriggered.emit()
    def onRemove(self):
        self.removeTriggered.emit()

# ------------------------------------------------------------------------------
#  Models
# ------------------------------------------------------------------------------

class BaseTableModel(QAbstractTableModel):
    """Abstract table model class to be inherited to display table data."""

    ColumnSpec = namedtuple('ColumnSpec', 'title, key, format, alignment, headerAlignment')

    def __init__(self, values, parent = None):
        super(BaseTableModel, self).__init__(parent)
        self.values = values
        self.columnSpecs = []

    def addColumnSpec(self, title, key, format = str, alignment = AlignLeft, headerAlignment = AlignCenter):
        spec = self.ColumnSpec(title, key, format, alignment, headerAlignment)
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
            if role == Qt.TextAlignmentRole:
                return self.columnSpecs[section].headerAlignment
        return QVariant()

# HACK
class Delegate(QStyledItemDelegate):
    def createEditor(self, parent, options, index):
        return QTextEdit(parent)
    def setEditorData(self, editor, index):
        editor.setText(index.data())
    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText())

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
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.menu.menu.items()[row][column]
        return QVariant()

    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid():
            return False
        row, column = index.row(), index.column()
        if role == Qt.EditRole:
            # brrr
            self.menu.menu[self.menu.menu.items()[row][0]] = str(value.toPyObject())
            self.dataChanged.emit(index, index)
            return True
        return False

    def setModelData(self, editor, model, index):
        if not index.isValid():
            return QVariant()
        if index.column() == 1:
            if isinstance(editor, QTextEdit):
                model.setData(index, editor.toPlainText())
            elif isinstance(editor, QComboBox):
                model.setData(index, editor.currentText())
            else:
                super(Delegate, self).setModelData(editor, model, index)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return ("Key", "Value")[section]
        return QVariant()

    def flags(self, index):
        if index.column() == 1:
            return super(MenuModel, self).flags(index) | Qt.ItemIsEditable
        return super(MenuModel, self).flags(index)

class AlgorithmsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(AlgorithmsModel, self).__init__(menu.algorithms, parent)
        self.formatter = AlgorithmFormatter()
        self.addColumnSpec("Index", 'index', int, AlignRight)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Expression", 'expression', fAlgorithm)
        # self.addColumnSpec("Comment", 'comment')

class CutsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(CutsModel, self).__init__(menu.cuts, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Object", 'object')
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
        self.addColumnSpec("Data", 'data')
        # self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'cut_id', int, AlignRight)

class ObjectsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ObjectsModel, self).__init__(menu.objects, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Comparison", 'comparison_operator', fComparison, AlignRight)
        self.addColumnSpec("Threshold", 'threshold', fThreshold, AlignRight)
        self.addColumnSpec("BX Offset", 'bx_offset', fBxOffset, AlignRight)
        self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'object_id', int, AlignRight)

class ExternalsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ExternalsModel, self).__init__(menu.externals, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("BX Offset", 'bx_offset', fBxOffset, AlignRight)
        self.addColumnSpec("Comment", 'comment')
        self.addColumnSpec("Timestamp", 'datetime')
        self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'requirement_id', int, AlignRight, AlignRight)
        # self.addColumnSpec("ID2", 'ext_signal_id', int, AlignRight)

class BinsModel(BaseTableModel):

    def __init__(self, menu, name, parent = None):
        super(BinsModel, self).__init__(menu.scales.bins[name], parent)
        self.name = name
        self.addColumnSpec("Number dec", 'number', int, AlignRight)
        self.addColumnSpec("Number hex", 'number', fHex, AlignRight)
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
        self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'scale_id', int, AlignRight, AlignRight)

class ExtSignalsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ExtSignalsModel, self).__init__(menu.extSignals.extSignals, parent)
        self.addColumnSpec("System", 'system')
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Label", 'label')
        self.addColumnSpec("Cable", 'cable')
        self.addColumnSpec("Channel", 'channel')
        self.addColumnSpec("Description", 'description')
        # self.addColumnSpec("ID", 'ext_signal_id', int, AlignRight)
