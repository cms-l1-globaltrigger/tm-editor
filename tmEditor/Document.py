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
from tmEditor import Settings

from tmEditor import CutEditorDialog
from tmEditor import AlgorithmEditorDialog
from tmEditor import AlgorithmSyntaxHighlighter

from tmEditor import Menu
from tmEditor.Menu import Algorithm, Cut, Object, External, toObject
from tmEditor.CutEditor import EtaGraph, PhiGraph

from tmEditor.Models import *
from tmEditor.Proxies import *
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

import math
import sys, os

MaxAlgorithms = 512

# ------------------------------------------------------------------------------
#  Document widget
# ------------------------------------------------------------------------------

class Document(QWidget):
    """Document container widget used by MDI area.

    Document consists of pages listed in a tree view on the left. Adding pages
    requires assigning a top and a bottom widget to each page. Normally the top
    widget is either a generic table view or a more specific form widget whereas
    the bottom widget holds a versatile preview widget displaying details and
    actions for the above selected data set.
    """

    modified = pyqtSignal()
    """This signal is emitted whenever the content of the document changes."""

    CutSettings = Settings.cutSettings()

    def __init__(self, filename, parent = None):
        super(Document, self).__init__(parent)
        # Attributes
        self.loadMenu(filename)
        # Layout
        self.setContentsMargins(0, 0, 0, 0)
        # Create table views.
        algorithmsTableView = self.createProxyTableView("algorithmsTableView", AlgorithmsModel(self.menu(), self))
        algorithmsTableView.resizeColumnsToContents()
        cutsTableView = self.createProxyTableView("cutsTableView", CutsModel(self.menu(), self), proxyclass=CutsModelProxy)
        cutsTableView.resizeColumnsToContents()
        objectsTableView = self.createProxyTableView("objectsTableView", ObjectsModel(self.menu(), self), proxyclass=ObjectsModelProxy)
        objectsTableView.resizeColumnsToContents()
        externalsTableView = self.createProxyTableView("externalsTableView", ExternalsModel(self.menu(), self), proxyclass=ExternalsModelProxy)
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
        self.menuPage = self.addPage("Menu", menuView, self.bottomWidget)
        self.algorithmsPage = self.addPage("Algorithms", algorithmsTableView, self.bottomWidget, self.menuPage)
        self.cutsPage = self.addPage("Cuts", cutsTableView, self.bottomWidget, self.menuPage)
        self.objectsPage = self.addPage("Object Requirements", objectsTableView, self.bottomWidget, self.menuPage)
        self.externalsPage = self.addPage("External Requirements", externalsTableView, self.bottomWidget, self.menuPage)
        label = QLabel("Select a scale set...", self)
        label.setAutoFillBackground(True)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scalesPage = self.addPage("Scales", label, self.bottomWidget)
        self.scalesTypePages = {}
        for scale in self.menu().scales.bins.keys():
            self.scalesTypePages[scale] = self.addPage(scale, binsTableViews[scale], self.bottomWidget, self.scalesPage)
        self.extSignalsPage = self.addPage("External Signals", extSignalsTableView, self.bottomWidget)
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
        #self.bottomWidget.setText("<img style=\"float:left;\" src=\":icons/tm-editor.svg\"/><h1 style=\"margin-left:120px;\">Trigger Menu Editor</h1><p style=\"margin-left:120px;\"><em>Editing Level-1 Global Trigger Menus with ease</em></p>")

    def createProxyTableView(self, name, model, proxyclass=QSortFilterProxyModel):
        """Factory to create new QTableView view using a QSortFilterProxyModel."""
        proxyModel = proxyclass(self)
        proxyModel.setSourceModel(model)
        tableView = TableView(self)
        tableView.setObjectName(name)
        tableView.setStyleSheet("#{name} {{ border: 0; }}".format(**locals()))
        tableView.setModel(proxyModel)
        tableView.doubleClicked.connect(self.editItem)
        tableView.selectionModel().selectionChanged.connect(self.updateBottom)
        return tableView

    def addPage(self, name, top, bottom, parent = None):
        """Add page consisting of navigation tree entry, top and bottom widget."""
        page = Page(name, top, bottom, parent or self.navigationTreeWidget)
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
        self._menu.readXml(filename)

    def saveMenu(self, filename = None):
        """Save menu to filename."""
        # Warn before loosing cuts
        orphans = self._menu.orphanedCuts()
        if len(orphans) > 1:
            QMessageBox.information(self,
                self.tr("Found orphaned cuts"),
                QString("There are %1 orphaned cuts (<em>%2</em>, ...) that will be lost as they can't be saved to the XML file!").arg(len(orphans)).arg(orphans[0])
            )
        elif len(orphans):
            QMessageBox.information(self,
                self.tr("Found orphaned cut"),
                QString("There is one orphaned cut (<em>%1</em>) that will be lost as it can't be saved to the XML file!").arg(orphans[0])
            )
        filename = filename or self.filename()
        self._menu.menu['name'] = str(self.menuPage.top.nameLineEdit.text())
        self._menu.menu['comment'] = str(self.menuPage.top.commentTextEdit.toPlainText())
        self._menu.writeXml(filename)
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
        free = [i for i in range(MaxAlgorithms)]
        for algorithm in self.menu().algorithms:
            if int(algorithm.index) in free:
                free.remove(int(algorithm.index))
        return free

    def updateTop(self):
        index, item = self.getSelection()
        if item and hasattr(item.top, 'sortByColumn'):
            item.top.sortByColumn(0, Qt.AscendingOrder)
        self.topStack.setCurrentWidget(item.top)
        self.updateBottom()

    def updateBottom(self):
        index, item = self.getSelection()
        # Generic preview...
        if item is self.menuPage:
            text = []
            for key, value in self.menu().menu.items():
                if value == '\x00': value = "" # Overwrite NULL characters
                text.append("<strong>{key}:</strong> {value}<br/>".format(**locals()))
            item.bottom.setText(''.join(text))
            item.bottom.setButtonsEnabled(True)
        elif index and item and isinstance(item.top, TableView):
            data = dict([(key, value) for key, value in item.top.model().sourceModel().values[index.row()].items()]) # Local copy
            rows = item.top.selectionModel().selectedRows()
            if item is self.algorithmsPage:
                if 1 < len(rows):
                    item.bottom.setText("Selected {0} algorithms.".format(len(rows)))
                else:
                    item.bottom.loadAlgorithm(Algorithm(**data))
            elif item is self.cutsPage:
                if 1 < len(rows):
                    item.bottom.setText("Selected {0} cuts.".format(len(rows)))
                else:
                    item.bottom.loadCut(Cut(**data))
            elif item is self.objectsPage:
                if 1 < len(rows):
                    item.bottom.setText("Selected {0} object requiremetns.".format(len(rows)))
                else:
                    item.bottom.loadObject(Object(**data))
            elif item is self.externalsPage:
                if 1 < len(rows):
                    item.bottom.setText("Selected {0} external signals.".format(len(rows)))
                else:
                    item.bottom.loadExternal(External(**data))
            elif item in self.scalesTypePages.values():
                text = []
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
        item.bottom.clearNotice()
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
            item.bottom.setNotice(self.tr("New objects requirements are created directly in the algorithm editor."), Toolbox.createIcon("info"))
        elif item is self.externalsPage:
            item.bottom.toolbar.hide()
            item.bottom.setNotice(self.tr("New external requirements are created directly in the algorithm editor."), Toolbox.createIcon("info"))
        else:
            item.bottom.toolbar.hide()

    def importCuts(self, cuts):
        """Import cuts from another menu."""
        for cut in cuts:
            self.menu().addCut(**cut)
        self.cutsPage.top.model().setSourceModel(self.cutsPage.top.model().sourceModel())

    def importAlgorithms(self, algorithms):
        """Import algorithms from another menu."""
        for algorithm in algorithms:
            for cut in algorithm.cuts():
                if not self.menu().cutByName(cut):
                    raise RuntimeError("Missing cut {cut}, unable to to import algorithm {algorithm.name}".format(**locals()))
            import_index = 0
            original_name = algorithm.name
            while self.menu().algorithmByName(algorithm.name):
                name = "{original_name}_import{import_index}".format(**locals())
                algorithm['name'] = name
                import_index += 1
            if import_index:
                QMessageBox.information(self,
                    self.tr("Renamed algorithm"),
                    QString("Renamed algorithm <em>%1</em> to <em>%2</em> as the name is already used.").arg(original_name).arg(algorithm.name)
                )
            if self.menu().algorithmByIndex(algorithm.index):
                index = self.getUnusedAlgorithmIndices()[0]
                QMessageBox.information(self,
                    self.tr("Relocating algorithm"),
                    QString("Moving algorithm <em>%1</em> from already used index %2 to free index %3.").arg(algorithm.name).arg(algorithm.index).arg(index),
                )
                algorithm['index'] = index
            self.menu().addAlgorithm(**algorithm)
            self.menu().updateAlgorithm(algorithm)
        self.algorithmsPage.top.model().setSourceModel(self.algorithmsPage.top.model().sourceModel())
        self.algorithmsPage.top.resizeColumnsToContents()
        self.objectsPage.top.model().setSourceModel(self.objectsPage.top.model().sourceModel())
        self.objectsPage.top.resizeColumnsToContents()

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
        self.algorithmsPage.top.resizeColumnsToContents()
        # REBUILD INDEX
        self.updateBottom()
        self.modified.emit()
        self.objectsPage.top.model().setSourceModel(self.objectsPage.top.model().sourceModel())
        self.objectsPage.top.resizeColumnsToContents()
        self.externalsPage.top.model().setSourceModel(self.externalsPage.top.model().sourceModel())
        self.externalsPage.top.resizeColumnsToContents()
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
        self.menu().addCut(**dialog.newCut())
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
        self.objectsPage.top.resizeColumnsToContents()
        self.externalsPage.top.model().setSourceModel(self.externalsPage.top.model().sourceModel())
        self.externalsPage.top.resizeColumnsToContents()
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
        self.objectsPage.top.model().setSourceModel(self.objectsPage.top.model().sourceModel())
        self.objectsPage.top.resizeColumnsToContents()
        self.externalsPage.top.model().setSourceModel(self.externalsPage.top.model().sourceModel())
        self.externalsPage.top.resizeColumnsToContents()
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
        dialog.loadCut(self.menu().cuts[index.row()])
        dialog.setSuffix('_'.join([dialog.suffix, 'copy']))
        dialog.suffixLineEdit.setEnabled(True) # todo
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.setModified(True)
        self.menu().addCut(**dialog.newCut())
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
            self.objectsPage.top.model().setSourceModel(self.objectsPage.top.model().sourceModel())
            self.objectsPage.top.resizeColumnsToContents()
            self.externalsPage.top.model().setSourceModel(self.externalsPage.top.model().sourceModel())
            self.externalsPage.top.resizeColumnsToContents()
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

class Page(QTreeWidgetItem):

    def __init__(self, name, top, bottom, parent = None):
        super(Page, self).__init__(parent, [name])
        self.name = name
        self.top = top
        self.bottom = bottom
        if not isinstance(parent, Page):
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
        self.addButton = QPushButton(Toolbox.createIcon("list-add"), "Add...", self)
        self.addButton.clicked.connect(self.onAdd)
        layout.addWidget(self.addButton)
        layout.addStretch(10)
        self.editButton = QPushButton(Toolbox.createIcon("text-editor"), "Edit...", self)
        self.editButton.clicked.connect(self.onEdit)
        layout.addWidget(self.editButton)
        self.copyButton = QPushButton(Toolbox.createIcon("edit-copy"), "Copy...", self)
        self.copyButton.clicked.connect(self.onCopy)
        layout.addWidget(self.copyButton)
        self.removeButton = QPushButton(Toolbox.createIcon("list-remove"), "Remove", self)
        self.removeButton.clicked.connect(self.onRemove)
        layout.addWidget(self.removeButton)
        self.toolbar.setLayout(layout)
        self.notice = Toolbox.IconLabel(QIcon(), QString(), self)
        self.notice.setAutoFillBackground(True)
        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("BottomWidgetTextEdit")
        self.textEdit.setStyleSheet("""
        #BottomWidgetTextEdit {
            border: 0;
            background-color: #eee;
        }""")
        self.etaGraph = EtaGraph(self)
        self.etaGraphBox = QGroupBox(self.tr("Eta preview"), self)
        box = QVBoxLayout()
        box.addWidget(self.etaGraph)
        self.etaGraphBox.setLayout(box)
        self.etaGraphBox.setAlignment(Qt.AlignTop)
        self.etaGraphBox.setObjectName("EtaGraphBox")
        self.etaGraphBox.setStyleSheet("""
        #EtaGraphBox {
            background-color: #eee;
        }""")

        self.phiGraph = PhiGraph(self)
        self.phiGraphBox = QGroupBox(self.tr("Phi preview"), self)
        box = QVBoxLayout()
        box.addWidget(self.phiGraph)
        self.phiGraphBox.setLayout(box)
        self.phiGraphBox.setAlignment(Qt.AlignTop)
        self.phiGraphBox.setObjectName("PhiGraphBox")
        self.phiGraphBox.setStyleSheet("""
        #PhiGraphBox {
            background-color: #eee;
        }""")

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar, 0, 0, 1, 3)
        layout.addWidget(self.notice, 1, 0, 1, 3)
        layout.addWidget(self.textEdit, 2, 0)
        layout.addWidget(self.etaGraphBox, 2, 1)
        layout.addWidget(self.phiGraphBox, 2, 2)
        self.setLayout(layout)
        self.clearEtaGraph()
        self.clearPhiGraph()

    def reset(self):
        self.clearNotice()
        self.clearEtaGraph()
        self.clearPhiGraph()
        self.setText("")

    def setNotice(self, text, icon = None):
        self.notice.show()
        self.notice.icon.hide()
        self.notice.icon.clear()
        self.notice.setText(text)
        if icon:
            self.notice.icon.show()
            self.notice.setIcon(icon)

    def clearNotice(self):
        self.notice.hide()
        self.notice.icon.clear()
        self.notice.label.clear()

    def setButtonsEnabled(self, enabled):
        self.editButton.setEnabled(enabled)
        self.copyButton.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)

    def clearEtaGraph(self):
        #self.etaGraph.reset()
        self.etaGraphBox.hide()

    def clearPhiGraph(self):
        #self.phiGraph.reset()
        self.phiGraphBox.hide()

    def setEtaGraph(self, lower, upper):
        self.etaGraph.setRange(lower, upper)
        self.etaGraphBox.show()

    def setPhiGraph(self, lower, upper):
        self.phiGraph.setRange(lower, upper)
        self.phiGraphBox.show()

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

    # Load params from item

    def loadAlgorithm(self, algorithm):
        self.reset()
        # Format expression
        expression = fAlgorithm(algorithm.expression)
        text = []
        text.append("<h2>{algorithm.name} ({algorithm.index})</h2>")
        text.append("<p><strong>Expression:</strong></p>")
        text.append("<p><code>{expression}</code></p>")
        if algorithm.comment:
            text.append("<p><strong>Comment:</strong></p>")
            text.append("<p><code>{algorithm.comment}</code></p>")
        # List used objects.
        objects = algorithm.objects()
        if objects:
            text.append("<p><strong>Used objects:</strong></p>")
            text.append("<p><ul>")
            for object in objects:
                text.append("<li>{object}</li>".format(**locals()))
            text.append("</ul></p>")
        # List used objects.
        cuts = algorithm.cuts()
        if cuts:
            text.append("<p><strong>Used cuts:</strong></p>")
            text.append("<p><ul>")
            for cut in cuts:
                text.append("<li>{cut}</li>".format(**locals()))
            text.append("</ul></p>")
        # List used external signals.
        externals = algorithm.externals()
        if externals:
            text.append("<p><strong>Used externals:</strong></p>")
            text.append("<p><ul>")
            for external in externals:
                text.append("<li>{external}</li>".format(**locals()))
            text.append("</ul></p>")
        self.setText("".join(text).format(**locals()))

    def loadCut(self, cut):
        self.reset()
        # Format expression
        minimum = fCut(cut.minimum)
        maximum = fCut(cut.maximum)
        text = []
        text.append("<h2>{cut.name}</h2>")
        text.append("<p><strong>Type:</strong> {cut.object}</p>")
        if cut.data:
            fdata = []
            if cut.object == tmGrammar.comb:
                typename = cut.type
            else:
                typename = "{0}-{1}".format(cut.object, cut.type)
            data_ = filter(lambda entry: entry.name == typename, Settings.cutSettings())[0].data
            for n in cut.data.split(','):
                fdata.append("<li>[{1}] {0}</li>".format(data_[int(n)], int(n)))
            fdata = ''.join(fdata)
            text.append("<p><strong>Data:</strong></p><p><ul>{translation}</ul></p>".format(translation = fdata))
        else:
            text.append("<p><strong>Minimum:</strong> {minimum}</p>")
            text.append("<p><strong>Maximum:</strong> {maximum}</p>")
        if cut.comment:
            text.append("<p><strong>Comment:</strong></p>")
            text.append("<p><code>{cut.comment}</code></p>")
        self.setText("".join(text).format(**locals()))
        if cut.type == tmGrammar.ETA:
            self.setEtaGraph(float(cut.minimum), float(cut.maximum))
        elif cut.type == tmGrammar.PHI:
            self.setPhiGraph(float(cut.minimum), float(cut.maximum))

    def loadObject(self, object):
        self.reset()
        threshold = fThreshold(str(object.threshold))
        bx_offset = fBxOffset(object.bx_offset)
        text = []
        text.append("<h2>{object.name}</h2>")
        text.append("<p><strong>Type:</strong> {object.type}</p>")
        text.append("<p><strong>Threshold:</strong> {threshold}</p>")
        text.append("<p><strong>BX offset:</strong> {bx_offset}</p>")
        if object.comment:
            text.append("<p><strong>Comment:</strong></p>")
            text.append("<p><code>{object.comment}</code></p>")
        self.setText("".join(text).format(**locals()))

    def loadExternal(self, external):
        self.reset()
        bx_offset = fBxOffset(external.bx_offset)
        text = []
        text.append("<h2>{external.name}</h2>")
        text.append("<p><strong>BX offset:</strong> {bx_offset}</p>")
        if external.comment:
            text.append("<p><strong>Comment:</strong></p><p><code>{external.comment}</code></p>")
        self.setText("".join(text).format(**locals()))
