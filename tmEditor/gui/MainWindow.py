# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Main window class holding a MDI area.
"""

from tmEditor.gui.AboutDialog import AboutDialog
from tmEditor.gui.PreferencesDialog import PreferencesDialog
from tmEditor.gui.OpenUrlDialog import OpenUrlDialog
from tmEditor.gui.ImportDialog import ImportDialog

from tmEditor.gui.Document import Document
from tmEditor.gui.MdiArea import MdiArea

from tmEditor.core import Toolbox
from tmEditor.core.AlgorithmSyntaxValidator import AlgorithmSyntaxError

from PyQt4 import QtCore
from PyQt4 import QtGui

import random
import urllib2
import tempfile
import webbrowser
import logging
import sys, os, re

__all__ = ['MainWindow', ]

L1ContentsURL = "http://globaltrigger.hephy.at/upgrade/tme/userguide"
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

class MainWindow(QtGui.QMainWindow):

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

    def createActions(self):
        # Action for opening an existing file.
        self.openAct = QtGui.QAction(self.tr("&Open..."), self)
        self.openAct.setShortcut(QtGui.QKeySequence.Open)
        self.openAct.setStatusTip(self.tr("Open an existing file"))
        self.openAct.setIcon(Toolbox.createIcon("document-open"))
        self.openAct.triggered.connect(self.onOpen)
        # Action for opening a file from URL.
        self.openUrlAct = QtGui.QAction(self.tr("Open &URL..."), self)
        self.openUrlAct.setStatusTip(self.tr("Open a file from a remote location"))
        self.openUrlAct.setIcon(Toolbox.createIcon("emblem-downloads"))
        self.openUrlAct.triggered.connect(self.onOpenUrl)
        # Action for importing from another file.
        self.importAct = QtGui.QAction(self.tr("Import..."), self)
        self.importAct.setStatusTip(self.tr("Import from existing file"))
        self.importAct.setIcon(Toolbox.createIcon("document-import"))
        self.importAct.triggered.connect(self.onImport)
        # Action for saving the current file.
        self.saveAct = QtGui.QAction(self.tr("&Save"), self)
        self.saveAct.setShortcut(QtGui.QKeySequence.Save)
        self.saveAct.setStatusTip(self.tr("Save the current file"))
        self.saveAct.setIcon(Toolbox.createIcon("document-save"))
        self.saveAct.triggered.connect(self.onSave)
        # Action for saving the current file with a different name.
        self.saveAsAct = QtGui.QAction(self.tr("Save &As..."), self)
        self.saveAsAct.setShortcut(QtGui.QKeySequence.SaveAs)
        self.saveAsAct.setStatusTip(self.tr("Save the current file with a different name"))
        self.saveAsAct.setIcon(Toolbox.createIcon("document-save-as"))
        self.saveAsAct.triggered.connect(self.onSaveAs)
        # Action for closing the current file.
        self.closeAct = QtGui.QAction(self.tr("&Close"), self)
        self.closeAct.setShortcut(QtGui.QKeySequence.Close)
        self.closeAct.setStatusTip(self.tr("Close the current file"))
        self.closeAct.setIcon(Toolbox.createIcon("window-close"))
        self.closeAct.triggered.connect(self.onClose)
        # Action for quitting the program.
        self.quitAct = QtGui.QAction(self.tr("&Quit"), self)
        self.quitAct.setShortcut(QtGui.QKeySequence.Quit)
        self.quitAct.setStatusTip(self.tr("Quit the programm"))
        self.quitAct.setIcon(Toolbox.createIcon("application-exit"))
        self.quitAct.triggered.connect(self.close)
        # Preferences.
        self.preferencesAct = QtGui.QAction(self.tr("&Preferences"), self)
        self.preferencesAct.setStatusTip(self.tr("Configure the application"))
        self.preferencesAct.setIcon(Toolbox.createIcon("gtk-preferences"))
        self.preferencesAct.triggered.connect(self.onPreferences)
        # Open contents help URL.
        self.contentsAct = QtGui.QAction(self.tr("&Contents"), self)
        self.contentsAct.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F1))
        self.contentsAct.setStatusTip(self.tr("Open L1 Trigger Menu online manual"))
        self.contentsAct.setIcon(Toolbox.createIcon("help-about"))
        self.contentsAct.triggered.connect(self.onShowContents)
        # Action to raise about dialog.
        self.aboutAct = QtGui.QAction(self.tr("&About"), self)
        self.aboutAct.setStatusTip(self.tr("About this application"))
        self.aboutAct.triggered.connect(self.onShowAbout)

    def createMenus(self):
        """Create menus."""
        # File menu
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.openUrlAct)
        self.fileMenu.addSeparator()
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
        self.statusAlgorithms = QtGui.QLabel(self)
        self.statusCuts = QtGui.QLabel(self)
        self.statusObjects = QtGui.QLabel(self)
        self.statusExternals = QtGui.QLabel(self)
        self.statusBar().addPermanentWidget(self.statusAlgorithms)
        self.statusBar().addPermanentWidget(self.statusCuts)
        self.statusBar().addPermanentWidget(self.statusObjects)
        self.statusBar().addPermanentWidget(self.statusExternals)

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
        objects = len(document.menu().objects) if document else self.tr("--")
        externals = len(document.menu().externals) if document else self.tr("--")
        self.statusAlgorithms.setText(self.tr("Algorithms: %1").arg(algorithms))
        self.statusCuts.setText(self.tr("Cuts: %1").arg(cuts))
        self.statusObjects.setText(self.tr("Objects: %1").arg(objects))
        self.statusExternals.setText(self.tr("Externals: %1").arg(externals))

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

    def setRemoteTimeout(self, seconds):
        """Set remote timeout in second (loading documents from remote locations)."""
        self.remoteTimeout = seconds

    def loadDocument(self, filename):
        """Load document from file or remote loaction and add it to the MDI area."""
        try:
            # Test if filename is an URL.
            result = RegExUrl.match(filename)
            if result:
                dialog = QtGui.QProgressDialog(self)
                dialog.resize(300, dialog.height())
                dialog.setWindowTitle(self.tr("Downloading..."))
                dialog.setWindowModality(QtCore.Qt.WindowModal)
                dialog.show()
                QtGui.QApplication.processEvents()
                # Open remote URL
                u = urllib2.urlopen(filename, timeout=self.remoteTimeout)
                meta = u.info()
                # Get byte size of remote content.
                contentLength = meta.getheaders("Content-Length")
                #if not contentLength:
                #    raise RuntimeError("Unable to open URL")
                fileSize = int(contentLength[0]) if contentLength else 0
                #dialog.setMaximum(fileSize)
                logging.info("fetching %s bytes from %s", fileSize or '<unknown>', filename)
                dialog.setLabelText(self.tr("Receiving data..."))
                dialog.setMaximum(fileSize)
                try:
                    # Create a temorary file buffer.
                    with tempfile.NamedTemporaryFile(bufsize = fileSize or 2**21) as f:
                        receivedSize = 0
                        blockSize = 1024
                        while True:
                            buffer = u.read(blockSize)
                            if not buffer:
                                break
                            receivedSize += len(buffer)
                            f.write(buffer)
                            dialog.setLabelText(self.tr("Downloading %1...").arg(Toolbox.sizeof_format(receivedSize)))
                            QtGui.QApplication.processEvents()
                            if dialog.wasCanceled():
                                return
                            dialog.setValue(receivedSize);
                        # Reset file pointer so make sure document is read from
                        # begin. Note: do not close the temporary file as it
                        # will vanish (see python tempfile.NamedTemporaryFile).
                        f.seek(0)
                        dialog.close()
                        # Create document by reading temporary file.
                        document = Document(f.name, self)
                except Exception, e: # TODO
                    dialog.close()
                    logging.error("Failed to load XML menu: %s", str(e))
                    QtGui.QMessageBox.critical(self,
                        self.tr("Failed to load XML menu"), str(e))
                    return
            # Else it is a local filesystem path.
            else:
                try:
                    document = Document(filename, self)
                except Exception, e: # TODO
                    logging.error("Failed to load XML menu: %s", str(e))
                    QtGui.QMessageBox.critical(self,
                        self.tr("Failed to load XML menu"), str(e))
                    raise
        except (RuntimeError, OSError), e:
            logging.error("Failed to open XML menu: %s", str(e))
            QtGui.QMessageBox.critical(self,
                self.tr("Failed to open XML menu"),
                str(e),
            )
        except urllib2.HTTPError, e:
            logging.error("Failed to download remote XML menu %s", filename)
            QtGui.QMessageBox.critical(self,
                self.tr("Failed to download remote XML menu"),
                self.tr("HTTP error, failed to download from %1").arg(filename),
            )
        except urllib2.URLError, e:
            logging.error("Failed to download remote XML menu %s", filename)
            QtGui.QMessageBox.critical(self,
                self.tr("Failed to download remote XML menu"),
                QtCore.QString("URL error, failed to download from %1").arg(filename),
            )
        else:
            index = self.mdiArea.addDocument(document)
            self.mdiArea.setCurrentIndex(index)

    def onOpen(self):
        """Select a XML menu file using an dialog."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        if self.mdiArea.currentDocument():
            path = os.path.dirname(self.mdiArea.currentDocument().filename())
        filenames = QtGui.QFileDialog.getOpenFileNames(self, self.tr("Open files..."),
            path, self.tr("L1-Trigger Menus (*%1)").arg(XmlFileExtension))
        for filename in filenames:
            self.loadDocument(str(filename))

    def onOpenUrl(self):
        """Select an URL to read XML file from."""
        dialog = OpenUrlDialog(self)
        dialog.setModal(True)
        dialog.loadRecentUrls()
        dialog.exec_()
        if dialog.result() != QtGui.QDialog.Accepted:
            return
        self.loadDocument(dialog.url())
        dialog.storeRecentUrls()

    def onImport(self):
        """Import algorithms from another XML file."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        if self.mdiArea.currentDocument():
            path = os.path.dirname(self.mdiArea.currentDocument().filename())
            filename = str(QtGui.QFileDialog.getOpenFileName(self, self.tr("Import file..."),
                path, self.tr("L1-Trigger Menus (*%1)").arg(XmlFileExtension)))
            if filename:
                try:
                    dialog = ImportDialog(filename, self.mdiArea.currentDocument().menu(), self)
                except AlgorithmSyntaxError, e:
                    QtGui.QMessageBox.critical(self, self.tr("Import error"), str(e))
                    return
                except (RuntimeError, ValueError), e:
                    QtGui.QMessageBox.critical(self, self.tr("Import error"), str(e))
                    return
                dialog.setModal(True)
                dialog.exec_()
                if dialog.result() != QtGui.QDialog.Accepted:
                    return
                # Import cuts and algorithms.
                try:
                    document = self.mdiArea.currentDocument()
                    document.importCuts(dialog.cuts)
                    document.importAlgorithms(dialog.algorithms)
                except (RuntimeError, ValueError), e:
                    QtGui.QMessageBox.critical(self, self.tr("Import error"), str(e))

    def onSave(self):
        document = self.mdiArea.currentDocument()
        try:
            document.saveMenu()
            self.mdiArea.setTabText(self.mdiArea.currentIndex(), document.name())
        except (RuntimeError, ValueError, IOError), e:
            QtGui.QMessageBox.critical(self,
                self.tr("Failed to write XML menu"), str(e))

    def onSaveAs(self):
        path = str(self.mdiArea.currentDocument().filename())
        if not path.endswith(XmlFileExtension):
            path = os.path.join(str(QtCore.QDir.homePath()), ''.join((os.path.basename(path), XmlFileExtension)))
        filename = str(QtGui.QFileDialog.getSaveFileName(self,
            self.tr("Save as..."), path,
            self.tr("L1-Trigger Menus (*%1)").arg(XmlFileExtension)))
        if filename:
            if not filename.endswith(XmlFileExtension):
                filename = ''.join((filename, XmlFileExtension))
            document = self.mdiArea.currentDocument()
            try:
                document.saveMenu(filename)
                # TODO
                self.mdiArea.setTabText(self.mdiArea.currentIndex(), document.name())
            except RuntimeError, e:
                QtGui.QMessageBox.critical(self,
                    self.tr("Failed to write XML menu"), str(e))
        self.syncActions()

    def onClose(self):
        """Removes the current active document."""
        index = self.mdiArea.currentIndex()
        self.mdiArea.closeDocument(index)

    def onShowContents(self):
        """Raise remote contents help."""
        webbrowser.open_new_tab(L1ContentsURL)

    def onPreferences(self):
        """Raise preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.exec_()

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
    app = QtGui.QApplication(sys.argv)
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
