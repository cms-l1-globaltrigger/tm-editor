# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Main window class holding a MDI area.
"""

from tmEditor import (
    AboutDialog,
    PreferencesDialog,
    OpenUrlDialog,
    ImportDialog,
    Document,
    MdiArea,
    Toolbox,
)

from PyQt4 import QtCore
from PyQt4 import QtGui

import random
import urllib2
import tempfile
import webbrowser
import logging
import sys, os, re

L1ContentsURL = "http://globaltrigger.hephy.at/upgrade/tme/userguide"

# NOTE: Bugfix for PyQt4.6
if not hasattr(QtGui.QKeySequence, 'Quit'):
    QtGui.QKeySequence.Quit = QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

# -----------------------------------------------------------------------------
#  Main window class
# -----------------------------------------------------------------------------

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent = None):
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
        algorithms = len(document.menu().algorithms) if document else '--'
        cuts = len(document.menu().cuts) if document else '--'
        objects = len(document.menu().objects) if document else '--'
        externals = len(document.menu().externals) if document else '--'
        self.statusAlgorithms.setText(QtCore.QString(" %1: %2 ").arg(self.tr("Algorithms")).arg(algorithms))
        self.statusCuts.setText(QtCore.QString(" %1: %2 ").arg(self.tr("Cuts")).arg(cuts))
        self.statusObjects.setText(QtCore.QString(" %1: %2 ").arg(self.tr("Objects")).arg(objects))
        self.statusExternals.setText(QtCore.QString(" %1: %2 ").arg(self.tr("Externals")).arg(externals))

    def syncActions(self):
        """Disable some actions if no document is opened."""
        enabled = bool(self.mdiArea.count())
        self.importAct.setEnabled(enabled)
        self.saveAct.setEnabled(enabled)
        self.saveAsAct.setEnabled(enabled)
        self.closeAct.setEnabled(enabled)
        # Make sure that the file is writeable (and exists)
        if enabled:
            document = self.mdiArea.currentDocument()
            self.saveAct.setEnabled(os.access(document.filename(), os.W_OK))

    def loadDocument(self, filename):
        """Load document from file or remote loaction and add it to the MDI area."""
        try:
            # Test if filename is an URL.
            result = re.match('\w+\:\/\/(.+)', filename)
            if result:
                # Open remote URL
                u = urllib2.urlopen(filename, timeout=4)
                meta = u.info()
                # Get byte size of remote content.
                contentLength = meta.getheaders("Content-Length")
                #if not contentLength:
                #    raise RuntimeError("Unable to open URL")
                fileSize = int(contentLength[0]) if contentLength else 0
                #dialog.setMaximum(fileSize)
                logging.info("fetching %s bytes from %s", fileSize or '<unknown>', filename)
                try:
                    dialog = QtGui.QProgressDialog("Downloading...", "Abort", 0, fileSize, self)
                    dialog.setWindowModality(QtCore.Qt.WindowModal)
                    dialog.show()
                    QtGui.QApplication.processEvents()
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
                            QtGui.QApplication.processEvents()
                            if dialog.wasCanceled():
                                return
                            dialog.setValue(receivedSize);
                        # Reset file pointer so make sure document is read from
                        # begin. Note: do not close the temporary file as it
                        # will vanish (see python tempfile.NamedTemporaryFile).
                        f.seek(0)
                        # Create document by reading temporary file.
                        document = Document(f.name, self)
                        dialog.close()
                except:
                    dialog.close()
                    raise
            # Else it is a local filesystem path.
            else:
                document = Document(filename, self)
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
            path, self.tr("L1-Trigger Menus (*.xml)"))
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
                path, self.tr("L1-Trigger Menus (*.xml)")))
            if filename:
                dialog = ImportDialog(filename, self.mdiArea.currentDocument().menu(), self)
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
                    QtGui.QMessageBox.critical(self,
                        self.tr("Import error"),
                        str(e),
                    )

    def onSave(self):
        document = self.mdiArea.currentDocument()
        try:
            document.saveMenu()
        except (RuntimeError, ValueError), e:
            QtGui.QMessageBox.critical(self,
                self.tr("Failed to write XML menu"),
                str(e),
            )

    def onSaveAs(self):
        path = str(self.mdiArea.currentDocument().filename())
        if not path.endswith('.xml'):
            path = os.path.join(str(QtCore.QDir.homePath()), ''.join((os.path.basename(path), '.xml')))
        filename = str(QtGui.QFileDialog.getSaveFileName(self, self.tr("Save as..."),
            path, self.tr("L1-Trigger Menus (*.xml)")))
        if filename:
            if not filename.endswith('.xml'):
                filename = ''.join((filename, '.xml'))
            document = self.mdiArea.currentDocument()
            try:
                document.saveMenu(filename)
                # TODO
                self.mdiArea.setTabText(self.mdiArea.currentIndex(), os.path.basename(filename))
            except RuntimeError, e:
                QtGui.QMessageBox.critical(self,
                    self.tr("Failed to write XML menu"),
                    str(e),
                )
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
#  Main application routine
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
