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

import tmGrammar

from tmEditor import Toolbox

from tmEditor import CutEditorDialog
from tmEditor import AlgorithmEditorDialog
from tmEditor import AlgorithmFormatter
from tmEditor import AlgorithmSyntaxHighlighter

from tmEditor import Menu
from tmEditor.Menu import Algorithm, Object, toObject

from tmEditor.Models import *
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

import sys, os

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
        # Bottom widget
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
        # Stacks
        self.topStack = QStackedWidget(self)
        self.bottomStack = QStackedWidget(self)
        # Add navigation items.
        self.menuPage = self.addPage(self.navigationTreeWidget, "Menu", menuView, self.bottomWidget)
        self.algorithmsPage = self.addPage(self.menuPage, "Algorithms", algorithmsTableView, self.bottomWidget)
        self.cutsPage = self.addPage(self.menuPage, "Cuts", cutsTableView, self.bottomWidget)
        self.objectsPage = self.addPage(self.menuPage, "Objects", objectsTableView, self.bottomWidget)
        self.externalsPage = self.addPage(self.menuPage, "Externals", externalsTableView, self.bottomWidget)
        label = QLabel("Select a scale set...", self)
        label.setAutoFillBackground(True)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scalesPage = self.addPage(self.navigationTreeWidget, "Scales", label, self.bottomWidget)
        self.scalesTypePages = {}
        for scale in self.menu().scales.bins.keys():
            self.scalesTypePages[scale] = self.addPage(self.scalesPage, scale, binsTableViews[scale], self.bottomWidget)
        self.extSignalsPage = self.addPage(self.navigationTreeWidget, "External Signals", extSignalsTableView, self.bottomWidget)
        # Finsish navigation setup.
        self.navigationTreeWidget.expandItem(self.menuPage)
        self.navigationTreeWidget.itemSelectionChanged.connect(self.updateTop)
        self.navigationTreeWidget.setCurrentItem(self.menuPage)
        # Splitters
        self.vsplitter = SlimSplitter(Qt.Horizontal, self)
        self.vsplitter.setObjectName("vsplitter")
        self.vsplitter.setStyleSheet("#vsplitter { border: 0; background: #888; }")
        self.vsplitter.addWidget(self.navigationTreeWidget)
        self.vsplitter.setOpaqueResize(False)
        self.hsplitter = SlimSplitter(Qt.Vertical, self)
        self.hsplitter.addWidget(self.topStack)
        self.hsplitter.addWidget(self.bottomStack)
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
        self.menuPage.top.nameLineEdit.setText(self.menu().menu['name'])
        self.menuPage.top.commentTextEdit.setPlainText(self.menu().menu['comment'] if 'comment' in self.menu().menu else '')
        self.bottomWidget.setText("<img style=\"float:left;\" src=\":icons/tm-editor.svg\"/><h1 style=\"margin-left:120px;\">Trigger Menu Editor</h1><p style=\"margin-left:120px;\"><em>Editing Level-1 Global Trigger Menus with ease</em></p>")

    def createProxyTableView(self, name, model):
        """Factory to create new QTableView view using a QSortFilterProxyModel."""
        proxyModel = QSortFilterProxyModel(self)
        proxyModel.setSourceModel(model)
        tableView = TableView(self)
        tableView.setObjectName(name)
        tableView.setStyleSheet("#{name} {{ border: 0; }}".format(**locals()))
        tableView.setModel(proxyModel)
        tableView.doubleClicked.connect(self.editItem)
        tableView.selectionModel().selectionChanged.connect(self.updateBottom)
        return tableView

    def addPage(self, parent, name, top, bottom):
        page = NavigationItem(parent, name, top, bottom)
        if 0 > self.topStack.indexOf(top):
            self.topStack.addWidget(top)
        if 0 > self.bottomStack.indexOf(bottom):
            self.bottomStack.addWidget(bottom)
        return page

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
        self._menu.menu['name'] = str(self.menuPage.top.nameLineEdit.text())
        self._menu.menu['comment'] = str(self.menuPage.top.commentTextEdit.toPlainText())
        self._menu.saveXml(filename)
        self.setFilename(filename)
        self.setName(os.path.basename(filename))
        self.setModified(False)
        index, item = self.getSelection()
        item.top.update()

    def getSelection(self):
        items = self.navigationTreeWidget.selectedItems()
        if not len(items):
            return None, None
        item = items[0]
        if isinstance(item.top, QTableView):
            index = item.top.currentMappedIndex()
            return index, item
        return None, item

    def getUnusedAlgorithmIndices(self):
        free = [i for i in range(512)]
        for algorithm in self.menu().algorithms:
            if int(algorithm.index) in free:
                free.remove(int(algorithm.index))
        return free

    def updateTop(self):
        index, item = self.getSelection()
        # if 0 > self.topStack.indexOf(item.top):
        #     self.topStack.addWidget(item.top)
        if item and hasattr(item.top, 'sortByColumn'):
            item.top.sortByColumn(0, Qt.AscendingOrder)
        self.topStack.setCurrentWidget(item.top)
        self.updateBottom()

    def updateBottom(self):
        index, item = self.getSelection()
        # Generic preview...
        if index and item and isinstance(item.top, TableView):
            data = dict([(key, value) for key, value in item.top.model().sourceModel().values[index.row()].items()]) # Local copy
            text = []
            if item is self.algorithmsPage:
                rows = item.top.selectionModel().selectedRows()
                if 1 < len(rows):
                    text.append("Selected {0} algorithms.".format(len(rows)))
                else:
                    text.append("<h2>{name} ({index})</h2>")
                    text.append("<p><strong>Expression:</strong></p><p><code>{expression}</code></p>")
                    if 'comment' in data.keys() and data['comment']:
                        text.append("<p><strong>Comment:</strong></p><p><code>{comment}</code></p>")
            elif item is self.cutsPage:
                rows = item.top.selectionModel().selectedRows()
                if 1 < len(rows):
                    text.append("Selected {0} cuts.".format(len(rows)))
                else:
                    data['maximum'], data['minimum'] = fCut(data['maximum']), fCut(data['minimum'])
                    text.append("<h2>{name}</h2>")
                    text.append("<p><strong>Type:</strong> {object}</p>")
                    if data['data']:
                        fdata = []
                        if data['object'] == tmGrammar.comb:
                            typename = data['type']
                        else:
                            typename = "{0}-{1}".format(data['object'], data['type'])
                        CutSettings = [Toolbox.CutSpec(**cut) for cut in Toolbox.Settings['cuts']]
                        data_ = filter(lambda entry: entry.name == typename, CutSettings)[0].data
                        for n in data['data'].split(','):
                            fdata.append("{0} ({1})".format(data_[int(n)], int(n)))
                        fdata = ', '.join(fdata)
                        text.append("<p><strong>Data:</strong> {translation}</p>".format(translation = fdata))
                    else:
                        text.append("<p><strong>Minimum:</strong> {minimum}</p>")
                        text.append("<p><strong>Maximum:</strong> {maximum}</p>")
                    if 'comment' in data.keys() and data['comment']:
                        text.append("<p><strong>Comment:</strong></p><p><code>{comment}</code></p>")
            elif item is self.objectsPage:
                rows = item.top.selectionModel().selectedRows()
                if 1 < len(rows):
                    text.append("Selected {0} object requiremetns.".format(len(rows)))
                else:
                    data['threshold'] = fThreshold(str(data['threshold']))
                    data['bx_offset'] = fBxOffset(data['bx_offset'])
                    text.append("<h2>{name}</h2>")
                    text.append("<p><strong>Type:</strong> {type}</p>")
                    text.append("<p><strong>Threshold:</strong> {threshold}</p>")
                    text.append("<p><strong>BX offset:</strong> {bx_offset}</p>")
            elif item is self.externalsPage:
                rows = item.top.selectionModel().selectedRows()
                if 1 < len(rows):
                    text.append("Selected {0} external signals.".format(len(rows)))
                else:
                    data['bx_offset'] = fBxOffset(data['bx_offset'])
                    text.append("<h2>{name}</h2>")
                    text.append("<p><strong>BX offset:</strong> {bx_offset}</p>")
                    if 'comment' in data.keys() and data['comment']:
                        text.append("<p><strong>Comment:</strong></p><p><code>{comment}</code></p>")
            elif item in self.scalesTypePages.values():
                data['name'] = item.name
                text.append("<h2>Scale {name}</h2>")
                text.append("<p><strong>Number:</strong> {number}</p>")
                data['maximum'], data['minimum'] = fCut(data['maximum']), fCut(data['minimum'])
                text.append("<p><strong>Minimum:</strong> {minimum}</p>")
                text.append("<p><strong>Maximum:</strong> {maximum}</p>")
            item.bottom.setText(''.join(text).format(**data))
            item.bottom.setButtonsEnabled(True)
        else:
            item.bottom.setText("Nothing selected...")
            item.bottom.setButtonsEnabled(False)
        item.bottom.notice.hide()
        item.bottom.toolbar.hide()
        #item.bottom.setText("")
        if item is self.algorithmsPage:
            item.bottom.toolbar.show()
        elif item is self.cutsPage:
            # Experimental - enable only possible controls
            item.bottom.toolbar.show()
            item.bottom.removeButton.setEnabled(False)
            if index:
                item.bottom.removeButton.setEnabled(True)
                cut = self.menu().cuts[index.row()]
                for algorithm in self.menu().algorithms:
                    if cut.name in algorithm.cuts():
                        item.bottom.removeButton.setEnabled(False)
        elif item is self.objectsPage:
            item.bottom.toolbar.hide()
            item.bottom.notice.setText(self.tr("<strong>Note:</strong> new objects are created directly in the algorithm editor."))
            item.bottom.notice.show()
        else:
            item.bottom.toolbar.hide()

    def addItem(self):
        try:
            index, item = self.getSelection()
            if item is self.algorithmsPage:
                self.addAlgorithm(index, item)
            elif item is self.cutsPage:
                self.addCut(index, item)
        except RuntimeError, e:
            QMessageBox.warning(self, "Error", str(e))

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
        self.menu().updateAlgorithm(self.menu().algorithmByName(algorithm.name)) # IMPORTANT: add/update new objects!
        item.top.model().setSourceModel(item.top.model().sourceModel())
        # REBUILD INDEX
        self.updateBottom()
        self.modified.emit()
        self.objectsPage.top.model().setSourceModel(self.objectsPage.top.model().sourceModel())
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
            minimum=dialog.minimum() if not dialog.data() else '',
            maximum=dialog.maximum() if not dialog.data() else '',
            data=dialog.data() if dialog.data() else '',
            comment=dialog.comment())
        self.cutsPage.top.model().setSourceModel(self.cutsPage.top.model().sourceModel())

    def editItem(self):
        try:
            index, item = self.getSelection()
            if item is self.algorithmsPage:
                self.editAlgorithm(index, item)
            elif item is self.cutsPage:
                self.editCut(index, item)
            self.updateBottom()
        except RuntimeError, e:
                QMessageBox.warning(self, "Error", str(e))

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
        self.updateBottom()
        self.modified.emit()
        self.menu().updateAlgorithm(algorithm)
        self.objectsPage.top.model().setSourceModel(self.objectsPage.top.model().sourceModel())
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
        self.cutsPage.top.model().setSourceModel(self.cutsPage.top.model().sourceModel())

    def copyItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsPage:
            self.copyAlgorithm(index, item)
        if item is self.cutsPage:
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
        item.top.model().setSourceModel(item.top.model().sourceModel())
        # REBUILD INDEX
        self.updateBottom()
        self.modified.emit()
        for name in algorithm.objects():
            if not filter(lambda item: item.name == name, self.menu().objects):
                self.menu().addObject(**toObject(name))
        self.objectsPage.top.model().setSourceModel(self.objectsPage.top.model().sourceModel())
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
        self.cutsPage.top.model().setSourceModel(self.cutsPage.top.model().sourceModel())

    def removeItem(self):
        index, item = self.getSelection()
        # Removing algorithm item
        if item is self.algorithmsPage:
            confirm = True
            while item.top.selectionModel().hasSelection():
                rows = item.top.selectionModel().selectedRows()
                row = rows[0]
                algorithm = item.top.model().sourceModel().values[item.top.model().mapToSource(row).row()]
                if confirm:
                    result = QMessageBox.question(self, "Remove algorithm",
                        QString("Do you want to remove algorithm <strong>%2, %1</strong> from the menu?").arg(algorithm.name).arg(algorithm.index),
                        QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.Abort if len(rows) > 1 else QMessageBox.Yes | QMessageBox.Abort)
                    if result == QMessageBox.Abort:
                        break
                    elif result == QMessageBox.YesToAll:
                        confirm = False
                item.top.model().removeRows(row.row(), 1)
            selection = item.top.selectionModel()
            selection.setCurrentIndex(selection.currentIndex(), QItemSelectionModel.Select | QItemSelectionModel.Rows)
            # Removing orphaned objects.
            for name in self.menu().orphanedObjects():
                object = self.menu().objectByName(name)
                self.menu().objects.remove(object)
            # REBUILD INDEX
            self.updateBottom()
            self.modified.emit()
            self.setModified(True)

        # Removing cut item
        elif item is self.cutsPage:
            confirm = True
            while item.top.selectionModel().hasSelection():
                rows = item.top.selectionModel().selectedRows()
                row = rows[0]
                cut = item.top.model().sourceModel().values[item.top.model().mapToSource(row).row()]
                for algorithm in self.menu().algorithms:
                    if cut.name in algorithm.cuts():
                        QMessageBox.warning(self,
                            self.tr("Cut is used"),
                            self.tr("Cut %1 is used by algorithm %2 an can not be removed. Remove the corresponding algorithm first.").arg(cut.name).arg(algorithm.name),
                        )
                        return
                if confirm:
                    result = QMessageBox.question(self, "Remove cut",
                        QString("Do you want to remove cut <strong>%1</strong> from the menu?").arg(cut.name),
                        QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.Abort if len(rows) > 1 else QMessageBox.Yes | QMessageBox.Abort)
                    if result == QMessageBox.Abort:
                        break
                    elif result == QMessageBox.YesToAll:
                        confirm = False
                item.top.model().removeRows(row.row(), 1)
            selection = item.top.selectionModel()
            selection.setCurrentIndex(selection.currentIndex(), QItemSelectionModel.Select | QItemSelectionModel.Rows)
            # REBUILD INDEX
            self.updateBottom()
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

    def __init__(self, parent, name, top, bottom):
        super(NavigationItem, self).__init__(parent, [name])
        self.name = name
        self.top = top
        self.bottom = bottom
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
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
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
        self.removeButton = QPushButton(Toolbox.createIcon('actions', 'list-remove'), "Delete", self)
        self.removeButton.clicked.connect(self.onRemove)
        layout.addWidget(self.removeButton)
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
            background-color: #eee;
        }""")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.notice)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

    def setToolbarVisible(self, visible):
        self.toolbar.setVisible(visible)

    def setNoticeVisible(self, visible):
        self.notice.setVisible(visible)

    def setButtonsEnabled(self, enabled):
        self.editButton.setEnabled(enabled)
        self.copyButton.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)

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
