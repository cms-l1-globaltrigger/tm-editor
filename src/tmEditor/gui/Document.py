"""Document widget."""

import logging
import copy
import os
import threading
from typing import List, Optional

from PyQt5 import QtCore, QtWidgets

from tmEditor.core import Settings
from tmEditor.core.Settings import MaxAlgorithms
from tmEditor.core import Menu
from tmEditor.core.Algorithm import Algorithm, Cut, toObject
from tmEditor.core import XmlDecoder, XmlEncoder
from tmEditor.core.XmlEncoder import XmlEncoderError
from tmEditor.core.XmlDecoder import XmlDecoderError

# Models and proxies for table views
from tmEditor.gui.models import *
from tmEditor.gui.proxies import *
from tmEditor.gui.views import *

from tmEditor.gui.CutEditorDialog import CutEditorDialog
from tmEditor.gui.AlgorithmEditorDialog import AlgorithmEditorDialog
from tmEditor.gui.AlgorithmSelectIndexDialog import AlgorithmSelectIndexDialog
from tmEditor.gui.BottomWidget import BottomWidget

# Common widgets
from tmEditor.gui.CommonWidgets import TextFilterWidget
from tmEditor.gui.CommonWidgets import RestrictedLineEdit
from tmEditor.gui.CommonWidgets import createIcon

__all__ = ["Document"]

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kCable = "cable"
kChannel = "channel"
kData = "data"
kDescription = "description"
kExpression = "expression"
kIndex = "index"
kLabel = "label"
kMaximum = "maximum"
kMinimum = "minimum"
kNBits = "n_bits"
kName = "name"
kNumber = "number"
kObject = "object"
kStep = "step"
kSystem = "system"
kType = "type"

def fScale(scale):
    """Rename muon scale for visualization."""
    # HACK ...
    if scale == "MU-ET":
        return "MU-PT"
    return scale

# HACK
def updateModel(model, context):
    """Workaround while fixing table models..."""
    source = model.sourceModel()
    model.setSourceModel(source.__class__(context.menu(), context))
    source.setParent(None)
    source.deleteLater()

def handleException(method):
    """Method decorator, show message box on exception."""
    def handleException(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Exception occured"),
                format(exc)
            )
    return handleException

# ------------------------------------------------------------------------------
#  Document widget
# ------------------------------------------------------------------------------

class BaseDocument(QtWidgets.QWidget):
    """Document container widget used by MDI area."""

    modified = QtCore.pyqtSignal()
    """This signal is emitted whenever the content of the document changes."""

    def __init__(self, filename, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setFilename(filename)
        self.setModified(False)

    def name(self):
        return self.__name

    def setName(self, name):
        self.__name = name

    def filename(self):
        return self.__filename

    def setFilename(self, filename):
        self.__filename = os.path.abspath(filename)

    def isModified(self):
        return self.__modified

    def setModified(self, modified):
        self.__modified = bool(modified)

class Document(BaseDocument):
    """Menu document container widget used by MDI area.

    Document consists of pages listed in a tree view on the left. Adding pages
    requires assigning a top and a bottom widget to each page. Normally the top
    widget is either a generic table view or a more specific form widget whereas
    the bottom widget holds a versatile preview widget displaying details and
    actions for the above selected data set.

        +-----+--QSplitter---------+
        |     | +--QSplitter-----+ |
        |     | | filterWidget   | |
        |     | +----------------+ |
        | [1] | | topStack       | |
        |     | +----------------+ |
        |     | | bottomWidget   | |
        |     | +----------------+ |
        +-----+--------------------+

        [1] navigationTreeWidget

    """

    def __init__(self, filename: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(filename, parent)
        # Attributes
        self.loadMenu(filename)
        # Layout
        self.setContentsMargins(0, 0, 0, 0)
        #
        self._pages: List = []
        # Filter bar
        self.filterWidget = TextFilterWidget(True, self)
        self.filterWidget.textChanged.connect(self.setFilterText)
        # Stacks
        self.topStack = QtWidgets.QStackedWidget(self)
        # Create table views.
        self.createNavigationTree()
        self.createBottomWidget()
        self.createMenuPage()
        self.createAlgorithmsPage()
        self.createCutsPage()
        self.createScalesPage()
        self.createScaleBinsPages()
        self.createExtSignalsPage()
        # Finsish navigation setup.
        self.navigationTreeWidget.expandItem(self.menuPage)
        self.navigationTreeWidget.setCurrentItem(self.menuPage)

        # Splitters

        self.vsplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        self.vsplitter.setHandleWidth(1)
        self.vsplitter.setContentsMargins(0, 0, 0, 0)
        self.vsplitter.setObjectName("vsplitter")
        self.vsplitter.setStyleSheet("#vsplitter { border: 0; background: #888; }")
        self.vsplitter.addWidget(self.navigationTreeWidget)
        self.vsplitter.setOpaqueResize(False)

        self.hsplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)
        self.hsplitter.setHandleWidth(1)
        self.hsplitter.setContentsMargins(0, 0, 0, 0)
        self.hsplitter.addWidget(self.filterWidget)
        self.hsplitter.addWidget(self.topStack)
        self.hsplitter.addWidget(self.bottomWidget)

        self.vsplitter.addWidget(self.hsplitter)
        self.vsplitter.setStretchFactor(0, 0)
        self.vsplitter.setStretchFactor(1, 1)
        self.vsplitter.setSizes([200, 600])
        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.vsplitter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createNavigationTree(self):
        self.navigationTreeWidget = QtWidgets.QTreeWidget(self)
        self.navigationTreeWidget.headerItem().setHidden(True)
        self.navigationTreeWidget.setObjectName("navigationTreeWidget")
        self.navigationTreeWidget.setStyleSheet("#navigationTreeWidget { border: 0; background: #eee; }")
        self.navigationTreeWidget.itemSelectionChanged.connect(self.updateTop)

    def createBottomWidget(self):
        self.bottomWidget = BottomWidget(self)
        self.bottomWidget.toolbar.addTriggered.connect(self.addItem)
        self.bottomWidget.toolbar.editTriggered.connect(self.editItem)
        self.bottomWidget.toolbar.copyTriggered.connect(self.copyItem)
        self.bottomWidget.toolbar.removeTriggered.connect(self.removeItem)
        self.bottomWidget.toolbar.moveTriggered.connect(self.moveItems)

    def createMenuPage(self):
        menuView = MenuWidget(self)
        menuView.loadMenu(self.menu())
        menuView.nameLineEdit.setText(self.menu().menu.name)
        menuView.commentTextEdit.setPlainText(self.menu().menu.comment)
        menuView.modified.connect(self.onModified)
        self.menuPage = self.addPage(self.tr("Menu"), menuView)

    def createAlgorithmsPage(self):
        model = AlgorithmsModel(self.menu(), self)
        tableView = self.newProxyTableView("algorithmsTableView", model)
        tableView.resizeColumnsToContents()
        self.algorithmsPage = self.addPage(self.tr("Algorithms/Seeds"), tableView, self.menuPage)
        self.algorithmsPage.setIcon(0, createIcon("expression"))

    def createCutsPage(self):
        model = CutsModel(self.menu(), self)
        tableView = self.newProxyTableView("cutsTableView", model, proxyclass=CutsModelProxy)
        tableView.resizeColumnsToContents()
        self.cutsPage = self.addPage(self.tr("Cuts"), tableView, self.menuPage)
        self.cutsPage.setIcon(0, createIcon("path-cut"))

    def createScalesPage(self):
        model = ScalesModel(self.menu(), self)
        tableView = self.newProxyTableView("scalesTableView", model, proxyclass=ScalesModelProxy)
        tableView.resizeColumnsToContents()
        self.scalesPage = self.addPage(self.tr("Scales"), tableView)

    def createExtSignalsPage(self):
        model = ExtSignalsModel(self.menu(), self)
        tableView = self.newProxyTableView("externalsTableView", model)
        tableView.resizeColumnsToContents()
        self.extSignalsPage = self.addPage(self.tr("External Signals"), tableView)

    def createScaleBinsPages(self):
        self.scalesTypePages = {}
        for scale in self.menu().scales.bins.keys():
            model = BinsModel(self.menu(), scale, self)
            tableView = self.newProxyTableView(f"{scale}TableView", model)
            self.scalesTypePages[scale] = self.addPage(fScale(scale), tableView, self.scalesPage)

    def newProxyTableView(self, name, model, proxyclass=QtCore.QSortFilterProxyModel):
        """Factory to create new QTableView view using a QSortFilterProxyModel."""
        proxyModel = proxyclass(self)
        proxyModel.setFilterKeyColumn(-1)
        proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        proxyModel.setSourceModel(model)
        tableView = TableView(self)
        tableView.setObjectName(name)
        tableView.setStyleSheet("#{0} {{ border: 0; }}".format(name))
        tableView.setModel(proxyModel)
        tableView.doubleClicked.connect(self.editItem)
        tableView.selectionModel().selectionChanged.connect(self.updateBottom)
        return tableView

    def addPage(self, name, top=None, parent: Optional[QtWidgets.QTreeWidgetItem] = None):
        """Add page consisting of navigation tree entry, top and bottom widget."""
        page = PageItem(name, top, self.bottomWidget, parent)
        if parent is None:
            self.navigationTreeWidget.addTopLevelItem(page)
        if 0 > self.topStack.indexOf(top):
            self.topStack.addWidget(top)
        self._pages.append(page)
        return page

    def setFilterText(self, text):
        index, item = self.getSelection()
        excludedPages = [self.menuPage, ]
        if item not in excludedPages:
            item.top.model().setFilterFixedString(text)

    @QtCore.pyqtSlot()
    def onModified(self) -> None:
        self.setModified(True)
        self.modified.emit()

    def menu(self):
        return self._menu

    def loadMenu(self, filename: str) -> None:
        """Load menu from filename, setup new document."""
        self.setFilename(filename)
        self.setName(os.path.basename(self.filename()))
        try:
            dialog = QtWidgets.QProgressDialog(self)
            dialog.setWindowTitle(self.tr("Loading..."))
            dialog.setCancelButton(None)
            dialog.setWindowModality(QtCore.Qt.WindowModal)
            dialog.resize(260, dialog.height())
            dialog.show()
            QtWidgets.QApplication.processEvents()
            # Create XML decoder and run
            queue = XmlDecoder.XmlDecoderQueue(self.filename())
            try:
                for callback in queue:
                    dialog.setLabelText(self.tr("{0}...").format(queue.message().capitalize()))
                    logging.debug("processing: %s...", queue.message())
                    QtWidgets.QApplication.sendPostedEvents(dialog, 0)
                    QtWidgets.QApplication.processEvents()
                    callback()
                    dialog.setValue(queue.progress())
                    QtWidgets.QApplication.processEvents()
            except XmlDecoderError as exc:
                raise
        except Exception:
            dialog.close()
            raise
        self._menu = queue.menu
        if queue.applied_mirgrations:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setWindowTitle(self.tr("Migration report"))
            msgBox.setText(self.tr(f"The loaded XML document has been migrated to the most recent grammar <strong>version {Menu.GrammarVersion}</strong>"))
            messages = [
                f"in file {filename!r}"
            ]
            for migration in queue.applied_mirgrations:
                if isinstance(migration.subject, Cut):
                    if migration.param == "object":
                        message = f"in cut {migration.subject.name!r}:\n" \
                                  f"  in attribute {migration.param!r}: removed obsolete entry {migration.before!r}"
                        messages.append(message)
                    else:
                        message = f"in cut {migration.subject.name!r}:\n" \
                                  f"  in attribute {migration.param!r}: {migration.before!r} => {migration.after!r}"
                        messages.append(message)
                elif isinstance(migration.subject, Algorithm):
                    message = f"in algorithm {migration.subject.name!r}:\n  " \
                              f"  in attribute {migration.param!r}: {migration.before!r} => {migration.after!r}"
                    messages.append(message)
            msgBox.setDetailedText("\n\n".join(messages))
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgBox.exec_()
        self.setModified(False)

    def saveMenu(self, filename=None):
        """Save menu to filename."""
        # Warn before loosing cuts
        orphans = self._menu.orphanedCuts()
        if len(orphans) > 1:
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Found orphaned cuts"),
                self.tr("There are {0} orphaned cuts (<em>{1}</em>, ...) that will be lost as they can't be saved to the XML file!").format(len(orphans), orphans[0])
            )
        elif len(orphans):
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Found orphaned cut"),
                self.tr("There is one orphaned cut (<em>{0}</em>) that will be lost as it can't be saved to the XML file!").format(orphans[0])
            )
        filename = filename or self.filename()
        # Update meta information
        self._menu.menu.name = self.menuPage.top.nameLineEdit.text()
        self._menu.menu.comment = self.menuPage.top.commentTextEdit.toPlainText()
        # Process dialog
        dialog = QtWidgets.QProgressDialog(self)
        dialog.setWindowTitle(self.tr("Saving..."))
        dialog.setCancelButton(None)
        dialog.setWindowModality(QtCore.Qt.WindowModal)
        dialog.resize(260, dialog.height())
        dialog.show()
        QtWidgets.QApplication.processEvents()
        # Create XML encoder queue and run queue
        queue = XmlEncoder.XmlEncoderQueue(self._menu, filename)
        try:
            for callback in queue:
                dialog.setLabelText(self.tr("{0}...").format(queue.message().capitalize()))
                logging.debug("processing: %s...", queue.message())
                QtWidgets.QApplication.sendPostedEvents(dialog, 0)
                QtWidgets.QApplication.processEvents()
                callback()
                dialog.setValue(queue.progress())
                QtWidgets.QApplication.processEvents()
        except XmlEncoderError:
            dialog.close()
            raise
        dialog.close()
        # Update document
        self.setFilename(filename)
        self.setName(os.path.basename(filename))
        self.menuPage.top.loadMenu(self.menu())
        self.setModified(False)
        index, item = self.getSelection()
        item.top.update()
        self.updateBottom()

    def getSelection(self):
        """Returns tuple of index and item from selected table model item."""
        items = self.navigationTreeWidget.selectedItems()
        if not len(items):
            return None, None
        item = items[0]
        if isinstance(item.top, QtWidgets.QTableView):
            index = item.top.currentMappedIndex()
            return index, item
        return None, item

    def getUnusedAlgorithmIndices(self):
        """"""
        free = [i for i in range(MaxAlgorithms)]
        for algorithm in self.menu().algorithms:
            if int(algorithm.index) in free:
                free.remove(int(algorithm.index))
        return free

    def getUniqueAlgorithmName(self, basename="L1_Unnamed"):
        """Returns eiter *basename* if not already used in menu, else tries to
        find an unused basename with number suffix. Worst case returns just the
        basename.
        """
        name = basename
        if self.menu().algorithmByName(name):
            # Default name is already used, try to find a derivate
            for i in range(2, MaxAlgorithms):
                name = "{0}_{1}".format(basename, i)
                if not self.menu().algorithmByName(name):
                    return name # got unused name!
        return basename # no clue...

    def updateTop(self):
        index, item = self.getSelection()
        if item and hasattr(item.top, "sortByColumn"):
            item.top.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.topStack.setCurrentWidget(item.top)
        excludedPages = [self.menuPage, ]
        self.filterWidget.setEnabled(item not in excludedPages)
        self.filterWidget.setVisible(item not in excludedPages)
        self.filterWidget.filterLineEdit.setText("")
        self.setFilterText("")
        self.updateBottom()

    def updateBottom(self):
        index, item = self.getSelection()
        # Generic preview...
        if hasattr(item.bottom, "reset"):
            item.bottom.reset()
        self.bottomWidget.show()
        if item is self.algorithmsPage:
            item.bottom.toolbar.moveButton.show()
            item.bottom.toolbar.moveButton.setEnabled(True)
        else:
            item.bottom.toolbar.moveButton.hide()
        if item is self.menuPage:
            lines = []
            lines.append(self.tr("<p><strong>Scale Set:</strong> {}</p>").format(self.menu().scales.scaleSet[kName]))
            lines.append(self.tr("<p><strong>External Signal Set:</strong> {}</p>").format(self.menu().extSignals.extSignalSet[kName]))
            lines.append(self.tr("<p><strong>Menu UUID:</strong> {}</p>").format(self.menu().menu.uuid_menu))
            lines.append(self.tr("<p><strong>Grammar Version:</strong> {}</p>").format(self.menu().menu.grammar_version))
            item.bottom.setText("".join(lines))
            item.bottom.toolbar.setButtonsEnabled(False)
        elif index and item and isinstance(item.top, TableView): # ignores menu view
            data = item.top.model().sourceModel().values[index.row()]
            rows = len(item.top.selectionModel().selectedRows())

            # Disable edit/copy buttons on multiple selections
            if rows > 1:
                item.bottom.toolbar.setButtonsEnabled(False)
                item.bottom.toolbar.removeButton.setEnabled(True)
                if item is self.algorithmsPage:
                    item.bottom.toolbar.moveButton.setEnabled(True)
            else:
                item.bottom.toolbar.setButtonsEnabled(True)

            if item is self.algorithmsPage:
                if 1 < rows:
                    item.bottom.setText(self.tr("<p>Selected {} algorithms.</p>").format(rows))
                else:
                    item.bottom.loadAlgorithm(data, self.menu())
            elif item is self.cutsPage:
                if 1 < rows:
                    item.bottom.setText(self.tr("<p>Selected {} cuts.</p>").format(rows))
                else:
                    item.bottom.loadCut(data, self.menu())
            elif item is self.scalesPage:
                if 1 < rows:
                    item.bottom.setText(self.tr("<p>Selected {} scale sets.</p>").format(rows))
                else:
                    item.bottom.loadScale(data)
            elif item in self.scalesTypePages.values():
                if 1 < rows:
                    item.bottom.setText(self.tr("<p>Selected {} scale bins.</p>").format(rows))
                else:
                    item.bottom.loadScaleType(item.name, data)
            elif item is self.extSignalsPage:
                if 1 < rows:
                    item.bottom.setText(self.tr("<p>Selected {} external signals.</p>").format(rows))
                else:
                    item.bottom.loadSignal(data)
        else:
            item.bottom.reset()
            item.bottom.setText(self.tr("<p>Nothing selected...</p>"))
            item.bottom.toolbar.setButtonsEnabled(False)
        item.bottom.clearNotice()
        item.bottom.toolbar.hide()
        #item.bottom.setText("")
        if item is self.algorithmsPage:
            item.bottom.toolbar.show()
        elif item is self.cutsPage:
            # Experimental - enable only possible controls
            item.bottom.toolbar.show()
            item.bottom.toolbar.removeButton.setEnabled(False)
            if index:
                item.bottom.toolbar.removeButton.setEnabled(True)
                cut = self.menu().cuts[index.row()]
                # Disable edit and remove button for cuts already used in algorithms
                for algorithm in self.menu().algorithms:
                    if cut.name in algorithm.cuts():
                        item.bottom.toolbar.removeButton.setEnabled(False)
                        break
        else:
            item.bottom.toolbar.hide()

    def importCuts(self, cuts):
        """Import cuts from another menu, ignores if cut already present."""
        for cut in cuts:
            if not self.menu().cutByName(cut.name):
                cut.modified = True
                self.menu().addCut(cut)
        # HACK
        updateModel(self.cutsPage.top.model(), self)

    def importAlgorithms(self, algorithms):
        """Import algorithms from another menu."""
        for algorithm in algorithms:
            for cut in algorithm.cuts():
                if not self.menu().cutByName(cut):
                    raise RuntimeError(self.tr(f"Missing cut {cut}, unable to to import algorithm {algorithm.name}"))
            import_index = 0
            original_name = algorithm.name
            while self.menu().algorithmByName(algorithm.name):
                name = f"{original_name}_import{import_index}"
                algorithm.name = name
                import_index += 1
            if import_index:
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Renamed algorithm"),
                    self.tr("Renamed algorithm <em>{}</em> to <em>{}</em> as the name is already used.").format(original_name, algorithm.name)
                )
            if self.menu().algorithmByIndex(algorithm.index):
                unused_indices = self.getUnusedAlgorithmIndices()
                if not unused_indices:
                    raise RuntimeError(self.tr("Exceeding maximum number of allowed algorithms."))
                    return
                index = unused_indices[0]
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Relocating algorithm"),
                    self.tr("Moving algorithm <em>{}</em> from already used index {} to free index {}.").format(algorithm.name, algorithm.index, index)
                )
                algorithm.index = int(index)
            algorithm.modified = True
            self.menu().addAlgorithm(algorithm)
            self.menu().extendReferenced(algorithm)
        # HACK
        updateModel(self.algorithmsPage.top.model(), self)
        self.algorithmsPage.top.resizeColumnsToContents()

    def addItem(self):
        try:
            index, item = self.getSelection()
            if item is self.algorithmsPage:
                self.addAlgorithm(index, item)
            elif item is self.cutsPage:
                self.addCut(index, item)
        except RuntimeError as exc:
            QtWidgets.QMessageBox.warning(self, self.tr("Error"), format(exc))
        item.top.sortByColumn(0, QtCore.Qt.AscendingOrder)
        selectedeRows = item.top.selectionModel().selectedRows()
        if selectedeRows:
            item.top.scrollTo(selectedeRows[0])

    def addAlgorithm(self, index, item):
        available_indices = self.getUnusedAlgorithmIndices()
        if not available_indices:
            QtWidgets.QMessageBox.warning(self, self.tr("Error"), self.tr("Exceeding maximum number of {} algorithms.".format(MaxAlgorithms)))
            return
        dialog = AlgorithmEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.setIndex(available_indices[0])
        dialog.setName(self.getUniqueAlgorithmName(self.tr("L1_Unnamed")))
        dialog.editor.setModified(False)
        dialog.exec_()
        # HACK
        updateModel(self.cutsPage.top.model(), self)
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        self.setModified(True)
        algorithm = Algorithm(
            int(dialog.index()),
            dialog.name(),
            dialog.expression(),
            dialog.comment()
        )
        algorithm.modified = True
        for name in algorithm.cuts():
            if not list(filter(lambda item: item.name == name, self.menu().cuts)):
                raise RuntimeError("NO SUCH CUT AVAILABLE")
        self.menu().addAlgorithm(algorithm)
        self.menu().extendReferenced(self.menu().algorithmByName(algorithm.name)) # IMPORTANT: add/update new objects!
        # HACK
        updateModel(item.top.model(), self)
        self.algorithmsPage.top.resizeColumnsToContents()
        # REBUILD INDEX
        self.updateBottom()
        self.modified.emit()
        # Select new entry TODO: better to implement insertRow in model!
        proxy = item.top.model()
        for row in range(proxy.rowCount()):
            index = proxy.index(row, 1)
            if index.data() == algorithm.name:
                item.top.setCurrentIndex(index)
                break

    def addCut(self, index, item):
        dialog = CutEditorDialog(self.menu(), self)
        dialog.setupCuts(Settings.CutSpecs)
        dialog.setModal(True)
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        cut = dialog.newCut()
        self.menu().addCut(cut)
        # HACK
        updateModel(self.cutsPage.top.model(), self)
        self.updateBottom()
        self.setModified(True)
        self.modified.emit()
        # Select new entry TODO: better to implement insertRow in model!
        proxy = item.top.model()
        for row in range(proxy.rowCount()):
            index = proxy.index(row, 0)
            if index.data() == cut.name:
                item.top.setCurrentIndex(index)
                break

    def editItem(self):
        try:
            index, item = self.getSelection()
            if item is self.algorithmsPage:
                self.editAlgorithm(index, item)
            elif item is self.cutsPage:
                self.editCut(index, item)
            self.updateBottom()
        except RuntimeError as exc:
            QtWidgets.QMessageBox.warning(self, self.tr("Error"), format(exc))
        item.top.sortByColumn(0, QtCore.Qt.AscendingOrder)
        selectedeRows = item.top.selectionModel().selectedRows()
        if selectedeRows:
            item.top.scrollTo(selectedeRows[0])

    def editAlgorithm(self, index, item):
        algorithm = self.menu().algorithms[index.row()]
        dialog = AlgorithmEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.loadAlgorithm(algorithm)
        dialog.editor.setModified(False)
        dialog.exec_()
        # HACK
        updateModel(self.cutsPage.top.model(), self)
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        self.setModified(True)
        algorithm.modified = True
        dialog.updateAlgorithm(algorithm)
        for name in algorithm.cuts():
            if not list(filter(lambda item: item.name == name, self.menu().cuts)):
                raise RuntimeError("NO SUCH CUT AVAILABLE") # TODO
        # REBUILD INDEX
        self.updateBottom()
        self.modified.emit()
        self.menu().extendReferenced(algorithm)

    @handleException
    def editCut(self, index, item):
        cut = self.menu().cuts[index.row()]
        dialog = CutEditorDialog(self.menu(), self)
        dialog.setupCuts(Settings.CutSpecs)
        dialog.setModal(True)
        dialog.loadCut(cut)
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        self.setModified(True)
        dialog.updateCut(cut)
        self.updateBottom()
        self.modified.emit()

    @handleException
    def copyItem(self):
        index, item = self.getSelection()
        if item is self.algorithmsPage:
            self.copyAlgorithm(index, item)
        if item is self.cutsPage:
            self.copyCut(index, item)
        item.top.sortByColumn(0, QtCore.Qt.AscendingOrder)
        selectedeRows = item.top.selectionModel().selectedRows()
        if selectedeRows:
            item.top.scrollTo(selectedeRows[0])

    @handleException
    def copyAlgorithm(self, index, item):
        unused_indices = self.getUnusedAlgorithmIndices()
        if not unused_indices:
            QtWidgets.QMessageBox.warning(self, self.tr("Error"), self.tr("Exceeding maximum number of {} algorithms.".format(MaxAlgorithms)))
            return
        algorithm = copy.deepcopy(self.menu().algorithms[index.row()])
        dialog = AlgorithmEditorDialog(self.menu(), self)
        dialog.setModal(True)
        dialog.setIndex(unused_indices[0])
        dialog.setName(algorithm.name + "_copy")
        dialog.setExpression(algorithm.expression)
        dialog.editor.setModified(False)
        dialog.exec_()
        # HACK
        updateModel(self.cutsPage.top.model(), self)
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        algorithm.expression = dialog.expression()
        algorithm.index = int(dialog.index())
        algorithm.name = dialog.name()
        algorithm.modified = True
        for name in algorithm.cuts():
            if not list(filter(lambda item: item.name == name, self.menu().cuts)):
                raise RuntimeError("NO SUCH CUT AVAILABLE") # TODO
        for name in algorithm.externals():
            if not list(filter(lambda item: item.name == name, self.menu().externals)):
                raise RuntimeError("NO SUCH EXTERNAL AVAILABLE") # TODO
        self.menu().algorithms.append(algorithm)
        # HACK
        updateModel(item.top.model(), self)
        # REBUILD INDEX
        self.updateBottom()
        self.modified.emit()
        self.setModified(True)
        for name in algorithm.objects():
            if not list(filter(lambda item: item.name == name, self.menu().objects)):
                self.menu().addObject(toObject(name))
        # Select new entry TODO: better to implement insertRow in model!
        proxy = item.top.model()
        for row in range(proxy.rowCount()):
            index = proxy.index(row, 1)
            if index.data() == algorithm.name:
                item.top.setCurrentIndex(index)
                break

    @handleException
    def copyCut(self, index, item):
        dialog = CutEditorDialog(self.menu(), self)
        dialog.copyMode = True # TODO TODO TODO
        dialog.setupCuts(Settings.CutSpecs)
        dialog.setModal(True)
        dialog.loadCut(self.menu().cuts[index.row()])
        suffix = "{0}{1}".format(dialog.suffixLineEdit.text(), self.tr("_copy"))
        dialog.suffixLineEdit.setText(suffix)
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        cut = dialog.newCut()
        self.menu().addCut(cut)
        # HACK
        updateModel(self.cutsPage.top.model(), self)
        self.updateBottom()
        self.setModified(True)
        self.modified.emit()
        # Select new entry TODO: better to implement insertRow in model!
        proxy = item.top.model()
        for row in range(proxy.rowCount()):
            index = proxy.index(row, 0)
            if index.data() == cut.name:
                item.top.setCurrentIndex(index)
                break

    @handleException
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
                    result = QtWidgets.QMessageBox.question(
                        self,
                        self.tr("Remove algorithm"),
                        self.tr("Do you want to remove algorithm <strong>{0}, {1}</strong> from the menu?").format(algorithm.name, algorithm.index),
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.YesToAll | QtWidgets.QMessageBox.Abort if len(rows) > 1 else QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Abort
                    )
                    if result == QtWidgets.QMessageBox.Abort:
                        break
                    elif result == QtWidgets.QMessageBox.YesToAll:
                        confirm = False
                item.top.model().removeRows(row.row(), 1)
            selection = item.top.selectionModel()
            selection.setCurrentIndex(selection.currentIndex(), QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
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
                        QtWidgets.QMessageBox.warning(
                            self,
                            self.tr("Cut is used"),
                            self.tr("Cut {0} is used by algorithm {1} an can not be removed. Remove the corresponding algorithm first.").format(cut.name, algorithm.name)
                        )
                        return
                if confirm:
                    result = QtWidgets.QMessageBox.question(
                        self,
                        self.tr("Remove cut"),
                        self.tr("Do you want to remove cut <strong>{0}</strong> from the menu?").format(cut.name),
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.YesToAll | QtWidgets.QMessageBox.Abort if len(rows) > 1 else QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Abort
                    )
                    if result == QtWidgets.QMessageBox.Abort:
                        break
                    elif result == QtWidgets.QMessageBox.YesToAll:
                        confirm = False
                item.top.model().removeRows(row.row(), 1)
            selection = item.top.selectionModel()
            selection.setCurrentIndex(selection.currentIndex(), QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
            # REBUILD INDEX
            self.updateBottom()
            self.modified.emit()
            self.setModified(True)

    @handleException
    def moveItems(self):
        item = self.algorithmsPage
        indices = []
        if item.top.selectionModel().hasSelection():
            rows = item.top.selectionModel().selectedRows()
            for row in rows:
                algorithm = item.top.model().sourceModel().values[item.top.model().mapToSource(row).row()]
                indices.append(algorithm.index)
        reserved = [i for i in range(MaxAlgorithms) if self.menu().algorithmByIndex(i) is not None]
        dialog = AlgorithmSelectIndexDialog(self)
        dialog.setup(reserved, indices)
        dialog.setModal(True)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            logging.debug("moving algorithms:")
            for k, v in dialog.mapping.items():
                algorithm = self.menu().algorithmByIndex(k)
                logging.debug("%s => %s", algorithm.index, v)
                assert algorithm.index == k
                algorithm.index = v
                algorithm.modified = True
            self.setModified(True)
            self.modified.emit()
            item.top.sortByColumn(0, QtCore.Qt.AscendingOrder)
            selectedeRows = item.top.selectionModel().selectedRows()
            if selectedeRows:
                item.top.scrollTo(selectedeRows[0])
        self.update()

# ------------------------------------------------------------------------------
#  Navigation tree item
# ------------------------------------------------------------------------------

class PageItem(QtWidgets.QTreeWidgetItem):
    """Custom QTreeWidgetItem holding references to top and bottom widgets."""

    def __init__(self, name, top=None, bottom=None, parent: Optional[QtWidgets.QTreeWidgetItem] = None) -> None:
        super().__init__(parent)  # type: ignore
        self.setText(0, name)
        self.name = name
        self.top = top
        self.bottom = bottom
        if not isinstance(parent, PageItem):
            # Hilight root items in bold text.
            font = self.font(0)
            font.setBold(True)
            self.setFont(0, font)

# ------------------------------------------------------------------------------
#  Menu information widget
# ------------------------------------------------------------------------------

class MenuWidget(QtWidgets.QScrollArea):
    """Menu information widget providing inputs for name and comment, shows
    assigned scale set."""

    modified = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self.nameLabel: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self.nameLabel.setText(self.tr("Name"))

        self.nameLineEdit: QtWidgets.QLineEdit = RestrictedLineEdit(self)
        self.nameLineEdit.setPrefix("L1Menu_")
        self.nameLineEdit.setRegexPattern("L1Menu_[a-zA-Z0-9_]+")
        self.nameLineEdit.textEdited.connect(self.onModified)

        self.commentLabel: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self.commentLabel.setText(self.tr("Comment"))

        self.commentTextEdit: QtWidgets.QPlainTextEdit = QtWidgets.QPlainTextEdit(self)
        self.commentTextEdit.textChanged.connect(self.onModified)

        widget: QtWidgets.QWidget = QtWidgets.QWidget(self)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(widget)
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.nameLineEdit)
        layout.addWidget(self.commentLabel)
        layout.addWidget(self.commentTextEdit)
        layout.setStretch(3, 1)

        self.setAutoFillBackground(True)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setWidget(widget)

    def loadMenu(self, menu) -> None:
        """Load input values from menu."""
        self.nameLineEdit.setText(menu.menu.name)
        self.commentTextEdit.setPlainText(menu.menu.comment)

    def updateMenu(self, menu) -> None:
        """Update menu with values from inputs."""
        menu.menu.name = self.nameLineEdit.text()
        menu.menu.comment = self.commentTextEdit.toPlainText()

    @QtCore.pyqtSlot()
    def onModified(self) -> None:
        self.modified.emit()
