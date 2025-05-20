"""Main window class holding a MDI area."""

import logging
import os
import re
import tempfile
import threading
import webbrowser
from typing import Optional

from urllib.error import HTTPError, URLError

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.formatter import fFileSize
from ..core.AlgorithmSyntaxValidator import AlgorithmSyntaxError
from ..core.toolbox import DownloadHelper
from ..core.Settings import ContentsURL
from ..core.XmlEncoder import XmlEncoderError
from ..core.XmlDecoder import XmlDecoderError

from .AboutDialog import AboutDialog
from .PreferencesDialog import PreferencesDialog
from .OpenUrlDialog import OpenUrlDialog
from .ImportDialog import ImportDialog
from .CommonWidgets import createIcon

from .Document import Document
from .MdiArea import MdiArea

__all__ = ["MainWindow"]

logger = logging.getLogger(__name__)

XmlFileExtension: str = ".xml"

RegExUrl = re.compile(r"(\w+)\://(.+)")
"""Precompiled regular expression for matching URLs (protocol://path).
Returned groups are protocol and path.
"""


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setRemoteTimeout(10)
        self.setWindowIcon(QtGui.QIcon(":icons/tm-editor.svg"))

        self._createActions()
        self._createMenus()
        self._createToolbar()
        self._createStatusBar()

        self.mdiArea: MdiArea = MdiArea(self)
        self.mdiArea.currentChanged.connect(self.updateStatusBarCounters)
        self.setCentralWidget(self.mdiArea)

        self.updateStatusBarMessage(self.tr("Ready"))
        self.updateStatusBarCounters()
        self.syncActions()

        self.mdiArea.currentChanged.connect(self.syncActions)
        self.updateRecentFilesMenu()

    def _createActions(self) -> None:
        # Action for opening an existing file.
        self.openAct = QtGui.QAction(self.tr("&Open..."), self)
        self.openAct.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        self.openAct.setStatusTip(self.tr("Open an existing file"))
        self.openAct.setIcon(createIcon("document-open"))
        self.openAct.triggered.connect(self.onOpen)
        # Action for opening a file from URL.
        self.openUrlAct = QtGui.QAction(self.tr("Open &URL..."), self)
        self.openUrlAct.setStatusTip(self.tr("Open a file from a remote location"))
        self.openUrlAct.setIcon(createIcon("emblem-downloads"))
        self.openUrlAct.triggered.connect(self.onOpenUrl)
        # Action for importing from another file.
        self.importAct = QtGui.QAction(self.tr("Import..."), self)
        self.importAct.setStatusTip(self.tr("Import from existing file"))
        self.importAct.setIcon(createIcon("document-import"))
        self.importAct.triggered.connect(self.onImport)
        # Action for saving the current file.
        self.saveAct = QtGui.QAction(self.tr("&Save"), self)
        self.saveAct.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        self.saveAct.setStatusTip(self.tr("Save the current file"))
        self.saveAct.setIcon(createIcon("document-save"))
        self.saveAct.triggered.connect(self.onSave)
        # Action for saving the current file with a different name.
        self.saveAsAct = QtGui.QAction(self.tr("Save &As..."), self)
        self.saveAsAct.setShortcut(QtGui.QKeySequence.StandardKey.SaveAs)
        self.saveAsAct.setStatusTip(self.tr("Save the current file with a different name"))
        self.saveAsAct.setIcon(createIcon("document-save-as"))
        self.saveAsAct.triggered.connect(self.onSaveAs)
        # Action for closing the current file.
        self.closeAct = QtGui.QAction(self.tr("&Close"), self)
        self.closeAct.setShortcut(QtGui.QKeySequence.StandardKey.Close)
        self.closeAct.setStatusTip(self.tr("Close the current file"))
        self.closeAct.setIcon(createIcon("window-close"))
        self.closeAct.triggered.connect(self.onClose)
        # Action for quitting the program.
        self.quitAct = QtGui.QAction(self.tr("&Quit"), self)
        self.quitAct.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        self.quitAct.setStatusTip(self.tr("Quit the programm"))
        self.quitAct.setIcon(createIcon("application-exit"))
        self.quitAct.triggered.connect(self.close)
        # Preferences.
        self.preferencesAct = QtGui.QAction(self.tr("&Preferences"), self)
        self.preferencesAct.setStatusTip(self.tr("Configure the application"))
        self.preferencesAct.setIcon(createIcon("gtk-preferences"))
        self.preferencesAct.triggered.connect(self.onPreferences)
        # Open contents help URL.
        self.contentsAct = QtGui.QAction(self.tr("&Contents"), self)
        self.contentsAct.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_F1))
        self.contentsAct.setStatusTip(self.tr("Open L1 Trigger Menu online manual"))
        self.contentsAct.setIcon(createIcon("help-about"))
        self.contentsAct.triggered.connect(self.onShowContents)
        # Action to raise about Qt dialog.
        self.aboutQtAct = QtGui.QAction(self.tr("About &Qt"), self)
        self.aboutQtAct.setStatusTip(self.tr("About Qt framework"))
        self.aboutQtAct.triggered.connect(self.onShowAboutQt)
        # Action to raise about dialog.
        self.aboutAct = QtGui.QAction(self.tr("&About"), self)
        self.aboutAct.setStatusTip(self.tr("About this application"))
        self.aboutAct.triggered.connect(self.onShowAbout)

    def _createMenus(self) -> None:
        """Create menus."""
        # File menu
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.openUrlAct)
        self.fileMenu.addSeparator()
        self.recentFilesMenu = self.fileMenu.addMenu(self.tr("&Recent Files"))
        self.recentFilesSeparator = self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.importAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.closeAct)
        self.fileMenu.addAction(self.quitAct)
        # Edit menu
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.editMenu.addAction(self.preferencesAct)
        # Help menu
        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.helpMenu.addAction(self.contentsAct)
        self.helpMenu.addAction(self.aboutQtAct)
        self.helpMenu.addAction(self.aboutAct)

    def _createToolbar(self) -> None:
        """Create main toolbar and pin to top area."""
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.addAction(self.openAct)
        self.toolbar.addAction(self.openUrlAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.saveAct)
        self.toolbar.addAction(self.saveAsAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.importAct)

    def _createStatusBar(self) -> None:
        """Create status bar and populate with status labels."""
        self.statusBar()
        self.statusAlgorithms = QtWidgets.QLabel(self)
        self.statusCuts = QtWidgets.QLabel(self)
        self.statusBar().addPermanentWidget(self.statusAlgorithms)
        self.statusBar().addPermanentWidget(self.statusCuts)

    @QtCore.Slot(str)
    def updateStatusBarMessage(self, message: str) -> None:
        """Updates status bar message."""
        self.statusBar().showMessage(message)

    @QtCore.Slot()
    def updateStatusBarCounters(self) -> None:
        """Update status bar with data of current MDI document."""
        algorithms = self.tr("--")
        cuts = self.tr("--")
        document = self.mdiArea.currentDocument()
        if document:
            menu = document.menu()
            if menu:
                algorithms = format(len(menu.algorithms))
                cuts = format(len(menu.cuts))
        self.statusAlgorithms.setText(self.tr("Algorithms: {0}").format(algorithms))
        self.statusCuts.setText(self.tr("Cuts: {0}").format(cuts))

    @QtCore.Slot()
    def syncActions(self) -> None:
        """Disable some actions if no document is opened."""
        enabled: bool = self.mdiArea.count() > 0
        self.importAct.setEnabled(enabled)
        self.saveAct.setEnabled(enabled)
        self.saveAsAct.setEnabled(enabled)
        self.closeAct.setEnabled(enabled)
        # Make sure that the file is writeable (and exists)
        if enabled:
            document = self.mdiArea.currentDocument()
            if document:
                self.saveAct.setEnabled(os.access(document.filename(), os.W_OK))

    def loadRecentFiles(self) -> list[str]:
        """Returns recent files from application settings."""
        filenames = QtCore.QSettings().value("recent/files", [], list)
        if not isinstance(filenames, list):
            filenames = []
        return [str(filename) for filename in filenames]

    def storeRecentFiles(self, filenames: list[str]):
        """Store recent files to application settings."""
        QtCore.QSettings().setValue("recent/files", filenames or [])

    def insertRecentFile(self, filename: str, limit: int = 5) -> None:
        """Insert file to recent files history, remove duplicated entries from
        the list, update recent files menu."""
        filenames = self.loadRecentFiles()
        if filename in filenames:
            filenames.pop(filenames.index(filename)) # Remove same entry
        if filename:
            filenames.insert(0, filename)
        self.storeRecentFiles(filenames[:limit])

    def updateRecentFilesMenu(self) -> None:
        """Update recent files menu from application settings."""
        self.recentFilesMenu.clear()
        for filename in self.loadRecentFiles():
            action = self.recentFilesMenu.addAction(os.path.basename(filename))
            action.setStatusTip(self.tr("Open recent file \"{0}\"".format(filename)))
            action.setData(os.path.realpath(filename))
            action.triggered.connect(self.onOpenRecentFile)
        self.recentFilesMenu.setEnabled(not self.recentFilesMenu.isEmpty())
        self.recentFilesSeparator.setEnabled(not self.recentFilesMenu.isEmpty())

    def remoteTimeout(self) -> int:
        return self._remoteTimeout

    def setRemoteTimeout(self, seconds: int, /) -> None:
        """Set remote timeout in second (loading documents from remote locations)."""
        self._remoteTimeout = seconds

    def downloadDocument(self, url: str) -> None:
        """Download document to temporary file and load it."""
        dialog = QtWidgets.QProgressDialog(self)
        dialog.resize(300, dialog.height())
        dialog.setWindowTitle(self.tr("Downloading..."))
        try:
            # Create a temorary file buffer.
            with tempfile.NamedTemporaryFile() as fp:
                helper = DownloadHelper(fp)

                def onReceived(size):
                    formattedSize = fFileSize(size)
                    dialog.setLabelText(self.tr("Downloading {0}...").format(formattedSize))
                    dialog.setValue(size)

                helper.receivedChanged.connect(onReceived)
                helper.finished.connect(dialog.close)
                helper.urlopen(url, timeout=self.remoteTimeout())

                logger.info("fetching %s bytes from %s", helper.contentLength or "<unknown>", url)
                dialog.setLabelText(self.tr("Receiving data..."))
                dialog.setMaximum(helper.contentLength)

                thread = threading.Thread(target=helper)
                QtCore.QTimer.singleShot(100, thread.start)
                dialog.exec()

                # Reset file pointer so make sure document is read from
                # begin. Note: do not close the temporary file as it
                # will vanish (see python tempfile.NamedTemporaryFile).
                fp.seek(0)
                try:
                    # Create document by reading temporary file.
                    document = Document(fp.name, self)
                except (RuntimeError, OSError) as exc:
                    logger.error("Failed to open XML menu: %s", exc)
                    QtWidgets.QMessageBox.critical(
                        self,
                        self.tr("Failed to open XML menu"),
                        format(exc),
                    )
                else:
                    index = self.mdiArea.addDocument(document)
                    self.mdiArea.setCurrentIndex(index)
        except HTTPError as exc:
            logger.error("Failed to download remote XML menu %s, %s", url, format(exc))
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Failed to download remote XML menu"),
                self.tr("HTTP error, failed to download from {0}, {1}").format(url, format(exc))
            )
        except URLError as exc:
            logger.error("Failed to download remote XML menu %s, %s", url, format(exc))
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Failed to download remote XML menu"),
                self.tr("URL error, failed to download from {0}, {1}").format(url, format(exc))
            )
        finally:
            dialog.close()

    def loadDocument(self, filename: str) -> None:
        """Load document from file or remote loaction and add it to the MDI area."""
        try:
            # Test if filename is an URL.
            result = RegExUrl.match(filename)
            if result:
                url = filename
                self.downloadDocument(url)
                return
            # Else it is a local filesystem path.
            else:
                # Do no re-open a document, just raise its tab.
                duplicate = self.mdiArea.findDocument(filename)
                if duplicate:
                    self.mdiArea.setCurrentWidget(duplicate)
                    return
                document = Document(filename, self)
        except Exception as exc:
            logger.exception(exc)
            logger.error("Failed to open XML menu: %s", filename)
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Failed to open XML menu"),
                format(exc)
            )
        else:
            index = self.mdiArea.addDocument(document)
            self.mdiArea.setCurrentIndex(index)
            self.insertRecentFile(os.path.realpath(filename))
            self.updateRecentFilesMenu()

    @QtCore.Slot()
    def onOpen(self) -> None:
        """Select a XML menu file using an dialog."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        document = self.mdiArea.currentDocument()
        if document:
            path = os.path.dirname(document.filename())
        filenames, filter_ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            self.tr("Open files..."),
            path,
            self.tr("L1-Trigger Menus (*{0})").format(XmlFileExtension)
        )
        for filename in filenames:
            self.loadDocument(filename)

    @QtCore.Slot()
    def onOpenUrl(self) -> None:
        """Select an URL to read XML file from."""
        dialog = OpenUrlDialog(self)
        dialog.setModal(True)
        dialog.loadRecentUrls()
        dialog.exec_()
        if dialog.result() != dialog.DialogCode.Accepted:
            return
        self.loadDocument(dialog.url())
        dialog.storeRecentUrls()

    @QtCore.Slot()
    def onOpenRecentFile(self) -> None:
        """Open file by recent files action. Connect this slot with every recent
        file menu action."""
        action = self.sender()
        if action:
            self.loadDocument(action.data())  # type: ignore

    @QtCore.Slot()
    def onImport(self) -> None:
        """Import algorithms from another XML file."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        document = self.mdiArea.currentDocument()
        if not document:
            return
        menu = document.menu()
        if not menu:
            return
        path = os.path.dirname(document.filename())
        filenameAndFilter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Import file..."), path,
            self.tr("L1-Trigger Menus (*{0})").format(XmlFileExtension)
        )
        filename = filenameAndFilter[0]
        if filename:
            try:
                dialog = ImportDialog(filename, menu, self)
            except AlgorithmSyntaxError as exc:
                QtWidgets.QMessageBox.critical(
                    self,
                    self.tr("Import error"),
                    format(exc)
                )
                return
            except (XmlDecoderError, RuntimeError, ValueError) as exc:
                QtWidgets.QMessageBox.critical(
                    self,
                    self.tr("Import error"),
                    format(exc)
                )
                return
            dialog.setModal(True)
            dialog.exec_()
            if dialog.result() != dialog.DialogCode.Accepted:
                return
            # Import cuts and algorithms.
            try:
                document = self.mdiArea.currentDocument()
                if document:
                    document.importCuts(dialog.cuts)
                    document.importAlgorithms(dialog.algorithms)
            except (RuntimeError, ValueError) as exc:
                QtWidgets.QMessageBox.critical(
                    self,
                    self.tr("Import error"),
                    format(exc)
                )

    @QtCore.Slot()
    def onSave(self) -> None:
        document = self.mdiArea.currentDocument()
        if document:
            try:
                document.writeMenu(document.filename())
                self.mdiArea.setTabText(self.mdiArea.currentIndex(), document.name())
            except Exception as exc:
                logger.exception(exc)
                QtWidgets.QMessageBox.critical(
                    self,
                    self.tr("Failed to write XML menu"),
                    format(exc)
                )

    @QtCore.Slot()
    def onSaveAs(self) -> None:
        document = self.mdiArea.currentDocument()
        if document:
            path = document.filename()
            if not path.endswith(XmlFileExtension):
                path = os.path.join(QtCore.QDir.homePath(), "".join((os.path.basename(path), XmlFileExtension)))
            filename, filter_ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                self.tr("Save as..."), path,
                self.tr("L1-Trigger Menus (*{0})").format(XmlFileExtension)
            )
            if filename:
                if not filename.endswith(XmlFileExtension):
                    filename = "".join((filename, XmlFileExtension))
                if document:
                    try:
                        document.writeMenu(filename)
                        # TODO
                        self.mdiArea.setTabText(self.mdiArea.currentIndex(), document.name())
                        self.insertRecentFile(os.path.realpath(document.filename()))
                    except (XmlEncoderError, RuntimeError, ValueError, IOError) as exc:
                        QtWidgets.QMessageBox.critical(
                            self,
                            self.tr("Failed to write XML menu"),
                            format(exc)
                        )
        self.syncActions()
        self.updateRecentFilesMenu()

    @QtCore.Slot()
    def onClose(self) -> None:
        """Removes the current active document."""
        index = self.mdiArea.currentIndex()
        self.mdiArea.closeDocument(index)

    @QtCore.Slot()
    def onShowContents(self) -> None:
        """Raise remote contents help."""
        webbrowser.open_new_tab(ContentsURL)

    @QtCore.Slot()
    def onPreferences(self) -> None:
        """Raise preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.exec_()
        # In case history was cleared
        self.updateRecentFilesMenu()

    @QtCore.Slot()
    def onShowAboutQt(self) -> None:
        """Raise about Qt dialog."""
        QtWidgets.QMessageBox.aboutQt(self)

    @QtCore.Slot()
    def onShowAbout(self) -> None:
        """Raise about this application dialog."""
        dialog = AboutDialog(self)
        dialog.exec_()

    @QtCore.Slot(QtGui.QCloseEvent)
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """On window close event, close all open documents."""
        while self.mdiArea.count():
            if not self.mdiArea.closeCurrentDocument():
                event.ignore()
                return
        event.accept()
