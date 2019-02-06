# -*- coding: utf-8 -*-

"""Main window class holding a MDI area.
"""

from tmEditor.core.formatter import fFileSize
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxError
from tmEditor.core.toolbox import DownloadHelper
from tmEditor.core.Settings import ContentsURL
from tmEditor.core.XmlEncoder import XmlEncoderError
from tmEditor.core.XmlDecoder import XmlDecoderError

from tmEditor.gui.AboutDialog import AboutDialog
from tmEditor.gui.PreferencesDialog import PreferencesDialog
from tmEditor.gui.OpenUrlDialog import OpenUrlDialog
from tmEditor.gui.ImportDialog import ImportDialog
from tmEditor.gui.CommonWidgets import createIcon

from tmEditor.gui.Document import Document
from tmEditor.gui.MdiArea import MdiArea

from tmEditor.PyQt5Proxy import QtCore
from tmEditor.PyQt5Proxy import QtGui
from tmEditor.PyQt5Proxy import QtWidgets
from tmEditor.PyQt5Proxy import pyqt4_str
from tmEditor.PyQt5Proxy import pyqt4_toPyObject

try:
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import HTTPError, URLError

import random
import tempfile
import webbrowser
import logging
import sys, os, re

__all__ = ['MainWindow', ]

XmlFileExtension = '.xml'

RegExUrl = re.compile(r'(\w+)\://(.+)')
"""Precompiled regular expression for matching URLs (protocol://path).
Returned groups are protocol and path.
"""

# NOTE: Bugfix for PyQt4.6
if not hasattr(QtGui.QKeySequence, 'Quit'):
    QtGui.QKeySequence.Quit = QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

# -----------------------------------------------------------------------------
#  Main window class
# -----------------------------------------------------------------------------

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # Setup window.
        self.setWindowIcon(QtGui.QIcon(":icons/tm-editor.svg"))
        self.setWindowTitle(self.tr("L1-Trigger Menu Editor"))
        self.resize(800, 600)
        # Create actions and toolbars.
        self.createActions()
        self.createMenus()
        self.createToolbar()
        self.createStatusBar()
        # Create MDI area
        self.mdiArea = MdiArea(self)
        self.mdiArea.currentChanged.connect(self.updateStatusBarCounters)
        self.setCentralWidget(self.mdiArea)
        # Set remote timeout (seconds)
        self.remoteTimeout = 10
        # Initialize
        self.updateStatusBarMessage(self.tr("Ready"))
        self.updateStatusBarCounters()
        self.syncActions()
        # Setup connections.
        self.mdiArea.currentChanged.connect(self.syncActions)
        self.updateRecentFilesMenu()

    def createActions(self):
        # Action for opening an existing file.
        self.openAct = QtWidgets.QAction(self.tr("&Open..."), self)
        self.openAct.setShortcut(QtGui.QKeySequence.Open)
        self.openAct.setStatusTip(self.tr("Open an existing file"))
        self.openAct.setIcon(createIcon("document-open"))
        self.openAct.triggered.connect(self.onOpen)
        # Action for opening a file from URL.
        self.openUrlAct = QtWidgets.QAction(self.tr("Open &URL..."), self)
        self.openUrlAct.setStatusTip(self.tr("Open a file from a remote location"))
        self.openUrlAct.setIcon(createIcon("emblem-downloads"))
        self.openUrlAct.triggered.connect(self.onOpenUrl)
        # Action for importing from another file.
        self.importAct = QtWidgets.QAction(self.tr("Import..."), self)
        self.importAct.setStatusTip(self.tr("Import from existing file"))
        self.importAct.setIcon(createIcon("document-import"))
        self.importAct.triggered.connect(self.onImport)
        # Action for saving the current file.
        self.saveAct = QtWidgets.QAction(self.tr("&Save"), self)
        self.saveAct.setShortcut(QtGui.QKeySequence.Save)
        self.saveAct.setStatusTip(self.tr("Save the current file"))
        self.saveAct.setIcon(createIcon("document-save"))
        self.saveAct.triggered.connect(self.onSave)
        # Action for saving the current file with a different name.
        self.saveAsAct = QtWidgets.QAction(self.tr("Save &As..."), self)
        self.saveAsAct.setShortcut(QtGui.QKeySequence.SaveAs)
        self.saveAsAct.setStatusTip(self.tr("Save the current file with a different name"))
        self.saveAsAct.setIcon(createIcon("document-save-as"))
        self.saveAsAct.triggered.connect(self.onSaveAs)
        # Action for closing the current file.
        self.closeAct = QtWidgets.QAction(self.tr("&Close"), self)
        self.closeAct.setShortcut(QtGui.QKeySequence.Close)
        self.closeAct.setStatusTip(self.tr("Close the current file"))
        self.closeAct.setIcon(createIcon("window-close"))
        self.closeAct.triggered.connect(self.onClose)
        # Action for quitting the program.
        self.quitAct = QtWidgets.QAction(self.tr("&Quit"), self)
        self.quitAct.setShortcut(QtGui.QKeySequence.Quit)
        self.quitAct.setStatusTip(self.tr("Quit the programm"))
        self.quitAct.setIcon(createIcon("application-exit"))
        self.quitAct.triggered.connect(self.close)
        # Preferences.
        self.preferencesAct = QtWidgets.QAction(self.tr("&Preferences"), self)
        self.preferencesAct.setStatusTip(self.tr("Configure the application"))
        self.preferencesAct.setIcon(createIcon("gtk-preferences"))
        self.preferencesAct.triggered.connect(self.onPreferences)
        # Open contents help URL.
        self.contentsAct = QtWidgets.QAction(self.tr("&Contents"), self)
        self.contentsAct.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F1))
        self.contentsAct.setStatusTip(self.tr("Open L1 Trigger Menu online manual"))
        self.contentsAct.setIcon(createIcon("help-about"))
        self.contentsAct.triggered.connect(self.onShowContents)
        # Action to raise about dialog.
        self.aboutAct = QtWidgets.QAction(self.tr("&About"), self)
        self.aboutAct.setStatusTip(self.tr("About this application"))
        self.aboutAct.triggered.connect(self.onShowAbout)

    def createMenus(self):
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
        self.helpMenu.addAction(self.aboutAct)

    def createToolbar(self):
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

    def createStatusBar(self):
        """Create status bar and populate with status labels."""
        self.statusBar()
        self.statusAlgorithms = QtWidgets.QLabel(self)
        self.statusCuts = QtWidgets.QLabel(self)
        self.statusBar().addPermanentWidget(self.statusAlgorithms)
        self.statusBar().addPermanentWidget(self.statusCuts)

    @QtCore.pyqtSlot(str)
    def updateStatusBarMessage(self, message):
        """Updates status bar message."""
        self.statusBar().showMessage(message)

    @QtCore.pyqtSlot()
    def updateStatusBarCounters(self):
        """Update status bar with data of current MDI document."""
        document = self.mdiArea.currentDocument()
        algorithms = len(document.menu().algorithms) if document else self.tr("--")
        cuts = len(document.menu().cuts) if document else self.tr("--")
        self.statusAlgorithms.setText(pyqt4_str(self.tr("Algorithms: {0}")).format(algorithms))
        self.statusCuts.setText(pyqt4_str(self.tr("Cuts: {0}")).format(cuts))

    @QtCore.pyqtSlot()
    def syncActions(self):
        """Disable some actions if no document is opened."""
        enabled = self.mdiArea.count()
        self.importAct.setEnabled(enabled)
        self.saveAct.setEnabled(enabled)
        self.saveAsAct.setEnabled(enabled)
        self.closeAct.setEnabled(enabled)
        # Make sure that the file is writeable (and exists)
        if enabled:
            document = self.mdiArea.currentDocument()
            self.saveAct.setEnabled(os.access(document.filename(), os.W_OK))

    def loadRecentFiles(self):
        """Returns recent files from application settings."""
        filenames = pyqt4_toPyObject(QtCore.QSettings().value("recent/files")) or []
        return [pyqt4_str(filename) for filename in filenames]

    def storeRecentFiles(self, filenames):
        """Store recent files to application settings."""
        QtCore.QSettings().setValue("recent/files", filenames)

    def insertRecentFile(self, filename, limit=5):
        """Insert file to recent files history, remove duplicated entries from
        the list, update recent files menu."""
        filenames = self.loadRecentFiles()
        if filename in filenames:
            filenames.pop(filenames.index(filename)) # Remove same entry
        if filename:
            filenames.insert(0, filename)
        self.storeRecentFiles(filenames[:limit])

    def updateRecentFilesMenu(self):
        """Update recent files menu from application settings."""
        self.recentFilesMenu.clear()
        for filename in self.loadRecentFiles():
            action = self.recentFilesMenu.addAction(os.path.basename(filename))
            action.setStatusTip(self.tr("Open recent file \"{0}\"".format(filename)))
            action.setData(os.path.realpath(filename))
            action.triggered.connect(self.onOpenRecentFile)
        self.recentFilesMenu.setEnabled(not self.recentFilesMenu.isEmpty())
        self.recentFilesSeparator.setEnabled(not self.recentFilesMenu.isEmpty())

    def setRemoteTimeout(self, seconds):
        """Set remote timeout in second (loading documents from remote locations)."""
        self.remoteTimeout = seconds

    def downloadDocument(self, url):
        """Download document to temporary file and load it."""
        try:
            dialog = QtWidgets.QProgressDialog(self)
            dialog.resize(300, dialog.height())
            dialog.setWindowTitle(self.tr("Downloading..."))
            dialog.setWindowModality(QtCore.Qt.WindowModal)
            dialog.show()
            QtWidgets.QApplication.processEvents()

            helper = DownloadHelper()
            helper.urlopen(url, timeout=self.remoteTimeout)

            logging.info("fetching %s bytes from %s", helper.contentLength or "<unknown>", url)
            dialog.setLabelText(self.tr("Receiving data..."))
            dialog.setMaximum(helper.contentLength)

            def callback():
                """Callback for updating the progress dialog."""
                dialog.setLabelText(pyqt4_str(self.tr("Downloading {0}...")).format(fFileSize(helper.receivedSize)))
                dialog.setValue(helper.receivedSize)
                QtWidgets.QApplication.processEvents()
                if dialog.wasCanceled():
                    return False
                return True

            # Create a temorary file buffer.
            with tempfile.NamedTemporaryFile() as fp:
                helper.get(fp, callback)
                # Reset file pointer so make sure document is read from
                # begin. Note: do not close the temporary file as it
                # will vanish (see python tempfile.NamedTemporaryFile).
                fp.seek(0)
                dialog.close()
                try:
                    # Create document by reading temporary file.
                    document = Document(fp.name, self)
                except (RuntimeError, OSError) as e:
                    logging.error("Failed to open XML menu: %s", e)
                    QtWidgets.QMessageBox.critical(self,
                        self.tr("Failed to open XML menu"), format(e),
                    )
                    return
                else:
                    index = self.mdiArea.addDocument(document)
                    self.mdiArea.setCurrentIndex(index)
                    return
        except HTTPError as e:
            dialog.close()
            logging.error("Failed to download remote XML menu %s, %s", url, format(e))
            QtWidgets.QMessageBox.critical(self,
                self.tr("Failed to download remote XML menu"),
                pyqt4_str(self.tr("HTTP error, failed to download from {0}, {1}")).format(url, format(e))
            )
            return
        except URLError as e:
            dialog.close()
            logging.error("Failed to download remote XML menu %s, %s", url, format(e))
            QtWidgets.QMessageBox.critical(self,
                self.tr("Failed to download remote XML menu"),
                pyqt4_str(self.tr("URL error, failed to download from {0}, {1}")).format(url, format(e))
            )
            return

    def loadDocument(self, filename):
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
                try:
                    # Do no re-open a document, just raise its tab.
                    duplicate = self.mdiArea.findDocument(filename)
                    if duplicate:
                        self.mdiArea.setCurrentWidget(duplicate)
                        return
                    document = Document(filename, self)
                except Exception as e:
                    logging.error("Failed to load XML menu: %s", e)
                    QtWidgets.QMessageBox.critical(self,
                        self.tr("Failed to load XML menu"), format(e))
                    raise
        except (RuntimeError, OSError) as e:
            logging.error("Failed to open XML menu: %s", e)
            QtWidgets.QMessageBox.critical(self,
                self.tr("Failed to open XML menu"), format(e),
            )
        else:
            index = self.mdiArea.addDocument(document)
            self.mdiArea.setCurrentIndex(index)
            self.insertRecentFile(os.path.realpath(filename))
            self.updateRecentFilesMenu()

    def onOpen(self):
        """Select a XML menu file using an dialog."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        if self.mdiArea.currentDocument():
            path = os.path.dirname(self.mdiArea.currentDocument().filename())
        filenames, filter_ = QtWidgets.QFileDialog.getOpenFileNames(
            self, self.tr("Open files..."), path,
            pyqt4_str(self.tr("L1-Trigger Menus (*{0})")).format(XmlFileExtension)
        )
        for filename in filenames:
            self.loadDocument(pyqt4_str(filename))

    def onOpenUrl(self):
        """Select an URL to read XML file from."""
        dialog = OpenUrlDialog(self)
        dialog.setModal(True)
        dialog.loadRecentUrls()
        dialog.exec_()
        if dialog.result() != QtWidgets.QDialog.Accepted:
            return
        self.loadDocument(pyqt4_str(dialog.url()))
        dialog.storeRecentUrls()

    def onOpenRecentFile(self):
        """Open file by recent files action. Connect this slot with every recent
        file menu action."""
        action = self.sender()
        if action:
            filename = pyqt4_str(pyqt4_toPyObject(action.data()))
            self.loadDocument(filename)

    def onImport(self):
        """Import algorithms from another XML file."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        if self.mdiArea.currentDocument():
            path = os.path.dirname(self.mdiArea.currentDocument().filename())
            filenameAndFilter = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("Import file..."), path,
                pyqt4_str(self.tr("L1-Trigger Menus (*{0})")).format(XmlFileExtension)
            )
            filename = pyqt4_str(filenameAndFilter[0])
            if filename:
                try:
                    dialog = ImportDialog(filename, self.mdiArea.currentDocument().menu(), self)
                except AlgorithmSyntaxError as e:
                    QtWidgets.QMessageBox.critical(self, self.tr("Import error"), pyqt4_str(e))
                    return
                except (XmlDecoderError, RuntimeError, ValueError) as e:
                    QtWidgets.QMessageBox.critical(self, self.tr("Import error"), pyqt4_str(e))
                    return
                dialog.setModal(True)
                dialog.exec_()
                if dialog.result() != QtWidgets.QDialog.Accepted:
                    return
                # Import cuts and algorithms.
                try:
                    document = self.mdiArea.currentDocument()
                    document.importCuts(dialog.cuts)
                    document.importAlgorithms(dialog.algorithms)
                except (RuntimeError, ValueError) as e:
                    QtWidgets.QMessageBox.critical(self, self.tr("Import error"), pyqt4_str(e))

    def onSave(self):
        document = self.mdiArea.currentDocument()
        try:
            document.saveMenu()
            self.mdiArea.setTabText(self.mdiArea.currentIndex(), document.name())
        except (XmlEncoderError, RuntimeError, ValueError, IOError) as e:
            QtWidgets.QMessageBox.critical(self,
                self.tr("Failed to write XML menu"), format(e))

    def onSaveAs(self):
        path = self.mdiArea.currentDocument().filename()
        if not path.endswith(XmlFileExtension):
            path = os.path.join(pyqt4_str(QtCore.QDir.homePath()), ''.join((os.path.basename(path), XmlFileExtension)))
        filename, filter_ = QtWidgets.QFileDialog.getSaveFileName(self, self.tr("Save as..."), path,
            pyqt4_str(self.tr("L1-Trigger Menus (*{0})")).format(XmlFileExtension)
        )
        filename = pyqt4_str(filename)
        if filename:
            if not filename.endswith(XmlFileExtension):
                filename = ''.join((filename, XmlFileExtension))
            document = self.mdiArea.currentDocument()
            try:
                document.saveMenu(filename)
                # TODO
                self.mdiArea.setTabText(self.mdiArea.currentIndex(), document.name())
                self.insertRecentFile(os.path.realpath(document.filename()))
            except (XmlEncoderError, RuntimeError, ValueError, IOError) as e:
                QtWidgets.QMessageBox.critical(self,
                    self.tr("Failed to write XML menu"), format(e))
        self.syncActions()
        self.updateRecentFilesMenu()

    def onClose(self):
        """Removes the current active document."""
        index = self.mdiArea.currentIndex()
        self.mdiArea.closeDocument(index)

    def onShowContents(self):
        """Raise remote contents help."""
        webbrowser.open_new_tab(ContentsURL)

    def onPreferences(self):
        """Raise preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.exec_()
        # In case history was cleared
        self.updateRecentFilesMenu()

    def onShowAbout(self):
        """Raise about this application dialog."""
        dialog = AboutDialog(self.windowTitle(), self)
        dialog.exec_()

    def closeEvent(self, event):
        """On window close event, close all open documents."""
        while self.mdiArea.count():
            if not self.mdiArea.closeCurrentDocument():
                event.ignore()
                return
        event.accept()

# ------------------------------------------------------------------------------
#  Main application loop
# ------------------------------------------------------------------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("HEPHY");
    app.setApplicationName("Trigger Menu Editor");
    window = MainWindow()
    window.show()

    return app.exec_()

# -----------------------------------------------------------------------------
#  Application execution
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
