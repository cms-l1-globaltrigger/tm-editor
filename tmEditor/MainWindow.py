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
    OpenUrlDialog,
    ImportDialog,
    Document,
    MdiArea,
    Toolbox,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import random
import urllib2
import tempfile
import webbrowser
import logging
import sys, os, re

L1ContentsURL = "http://globaltrigger.hephy.at/upgrade/tme/userguide"

# NOTE: Bugfix for PyQt4.6
if not hasattr(QKeySequence, 'Quit'):
    QKeySequence.Quit = QKeySequence(Qt.CTRL + Qt.Key_Q)

# -----------------------------------------------------------------------------
#  Main window class
# -----------------------------------------------------------------------------

class MainWindow(QMainWindow):

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        # Setup window.
        self.setWindowIcon(QIcon(":icons/tm-editor.svg"))
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
        self.openAct = QAction(self.tr("&Open..."), self)
        self.openAct.setShortcut(QKeySequence.Open)
        self.openAct.setStatusTip(self.tr("Open an existing file"))
        self.openAct.setIcon(Toolbox.createIcon("document-open"))
        self.openAct.triggered.connect(self.onOpen)
        # Action for opening a file from URL.
        self.openUrlAct = QAction(self.tr("Open &URL..."), self)
        self.openUrlAct.setStatusTip(self.tr("Open a file from a remote location"))
        self.openUrlAct.setIcon(Toolbox.createIcon("emblem-downloads"))
        self.openUrlAct.triggered.connect(self.onOpenUrl)
        # Action for importing from another file.
        self.importAct = QAction(self.tr("Import..."), self)
        self.importAct.setStatusTip(self.tr("Import from existing file"))
        self.importAct.setIcon(Toolbox.createIcon("document-import"))
        self.importAct.triggered.connect(self.onImport)
        # Action for saving the current file.
        self.saveAct = QAction(self.tr("&Save"), self)
        self.saveAct.setShortcut(QKeySequence.Save)
        self.saveAct.setStatusTip(self.tr("Save the current file"))
        self.saveAct.setIcon(Toolbox.createIcon("document-save"))
        self.saveAct.triggered.connect(self.onSave)
        # Action for saving the current file with a different name.
        self.saveAsAct = QAction(self.tr("Save &As..."), self)
        self.saveAsAct.setShortcut(QKeySequence.SaveAs)
        self.saveAsAct.setStatusTip(self.tr("Save the current file with a different name"))
        self.saveAsAct.setIcon(Toolbox.createIcon("document-save-as"))
        self.saveAsAct.triggered.connect(self.onSaveAs)
        # Action for closing the current file.
        self.closeAct = QAction(self.tr("&Close"), self)
        self.closeAct.setShortcut(QKeySequence.Close)
        self.closeAct.setStatusTip(self.tr("Close the current file"))
        self.closeAct.setIcon(Toolbox.createIcon("window-close"))
        self.closeAct.triggered.connect(self.onClose)
        # Action for quitting the program.
        self.quitAct = QAction(self.tr("&Quit"), self)
        self.quitAct.setShortcut(QKeySequence.Quit)
        self.quitAct.setStatusTip(self.tr("Quit the programm"))
        self.quitAct.setIcon(Toolbox.createIcon("application-exit"))
        self.quitAct.triggered.connect(self.close)
        # Open contents help URL.
        self.contentsAction = QAction(self.tr("&Contents"), self)
        self.contentsAction.setShortcut(QKeySequence(Qt.Key_F1))
        self.contentsAction.setStatusTip(self.tr("Open L1 Trigger Menu online manual"))
        self.contentsAction.setIcon(Toolbox.createIcon("help-about"))
        self.contentsAction.triggered.connect(self.onShowContents)
        # Action to raise about dialog.
        self.aboutAction = QAction(self.tr("&About"), self)
        self.aboutAction.setStatusTip(self.tr("About this application"))
        self.aboutAction.triggered.connect(self.onShowAbout)

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
        # Help menu
        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.helpMenu.addAction(self.contentsAction)
        self.helpMenu.addAction(self.aboutAction)

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
        self.statusAlgorithms = QLabel(self)
        self.statusCuts = QLabel(self)
        self.statusObjects = QLabel(self)
        self.statusExternals = QLabel(self)
        self.statusBar().addPermanentWidget(self.statusAlgorithms)
        self.statusBar().addPermanentWidget(self.statusCuts)
        self.statusBar().addPermanentWidget(self.statusObjects)
        self.statusBar().addPermanentWidget(self.statusExternals)

    @pyqtSlot(str)
    def updateStatusBarMessage(self, message):
        """Updates status bar message."""
        self.statusBar().showMessage(message)

    @pyqtSlot()
    def updateStatusBarCounters(self):
        """Update status bar with data of current MDI document."""
        document = self.mdiArea.currentDocument()
        algorithms = len(document.menu().algorithms) if document else '--'
        cuts = len(document.menu().cuts) if document else '--'
        objects = len(document.menu().objects) if document else '--'
        externals = len(document.menu().externals) if document else '--'
        self.statusAlgorithms.setText(QString(" %1: %2 ").arg(self.tr("Algorithms")).arg(algorithms))
        self.statusCuts.setText(QString(" %1: %2 ").arg(self.tr("Cuts")).arg(cuts))
        self.statusObjects.setText(QString(" %1: %2 ").arg(self.tr("Objects")).arg(objects))
        self.statusExternals.setText(QString(" %1: %2 ").arg(self.tr("Externals")).arg(externals))

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
            # Test if filename is a remote URL.
            result = re.match('(http|https|ftp|file)\:\/\/(.+)', filename)
            if result:
                protocol, url = result.groups()
                # Handle file protocol as local filesystem path.
                if protocol == 'file':
                    document = Document(url, self)
                # Else try to download remote file to a temporary file.
                else:
                    url = filename
                    u = urllib2.urlopen(url)
                    meta = u.info()
                    # Get byte size of remote content.
                    contentLength = meta.getheaders("Content-Length")
                    #if not contentLength:
                    #    raise RuntimeError("Unable to open URL")
                    fileSize = int(contentLength[0]) if contentLength else 2**10
                    logging.info("fetching %s bytes from %s", fileSize, url)
                    dialog = ProgressDialog(fileSize, self)
                    dialog.setModal(True)
                    dialog.show()
                    try:
                        # Create a temorary file buffer.
                        with tempfile.NamedTemporaryFile(bufsize = fileSize) as f:
                            receivedSize = 0
                            blockSize = 1024 * 8
                            while True:
                                buffer = u.read(blockSize)
                                if not buffer:
                                    break
                                receivedSize += len(buffer)
                                f.write(buffer)
                                dialog.setReceivedSize(receivedSize)
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
        except (RuntimeError, OSError, urllib2.HTTPError, urllib2.URLError), e:
            QMessageBox.critical(self,
                self.tr("Failed to open XML menu"),
                str(e),
            )
        else:
            index = self.mdiArea.addDocument(document)
            self.mdiArea.setCurrentIndex(index)

    def onOpen(self):
        """Select a XML menu file using an dialog."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        if self.mdiArea.currentDocument():
            path = os.path.dirname(self.mdiArea.currentDocument().filename())
        filenames = QFileDialog.getOpenFileNames(self, self.tr("Open files..."),
            path, self.tr("L1-Trigger Menus (*.xml)"))
        for filename in filenames:
            self.loadDocument(str(filename))

    def onOpenUrl(self):
        """Select an URL to read XML file from."""
        dialog = OpenUrlDialog(self)
        dialog.setModal(True)
        dialog.loadRecentUrls()
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            return
        self.loadDocument(dialog.url())
        dialog.storeRecentUrls()

    def onImport(self):
        """Import algorithms from another XML file."""
        path = os.getcwd() # Default is user home dir on desktop environments.
        if self.mdiArea.currentDocument():
            path = os.path.dirname(self.mdiArea.currentDocument().filename())
            filename = str(QFileDialog.getOpenFileName(self, self.tr("Import file..."),
                path, self.tr("L1-Trigger Menus (*.xml)")))
            if filename:
                dialog = ImportDialog(filename, self.mdiArea.currentDocument().menu(), self)
                dialog.setModal(True)
                dialog.exec_()
                if dialog.result() != QDialog.Accepted:
                    return
                # Import cuts and algorithms.
                try:
                    document = self.mdiArea.currentDocument()
                    document.importCuts(dialog.cuts)
                    document.importAlgorithms(dialog.algorithms)
                except (RuntimeError, ValueError), e:
                    QMessageBox.critical(self,
                        self.tr("Import error"),
                        str(e),
                    )


    def onSave(self):
        document = self.mdiArea.currentDocument()
        try:
            document.saveMenu()
        except (RuntimeError, ValueError), e:
            QMessageBox.critical(self,
                self.tr("Failed to write XML menu"),
                str(e),
            )

    def onSaveAs(self):
        path = str(self.mdiArea.currentDocument().filename())
        if not path.endswith('.xml'):
            path = os.path.join(str(QDir.homePath()), ''.join((os.path.basename(path), '.xml')))
        filename = str(QFileDialog.getSaveFileName(self, self.tr("Save as..."),
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
                QMessageBox.critical(self,
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

#
# Download progress dialog.
#

class ProgressDialog(QDialog):
    """Dialog with progress bar displaying the donload progress."""

    def __init__(self, bytes, parent = None):
        super(ProgressDialog, self).__init__(parent)
        flags = self.windowFlags()
        flags &= ~Qt.WindowCloseButtonHint
        flags |= Qt.WindowMinimizeButtonHint
        self.setWindowFlags(flags)
        self.setWindowTitle(self.tr("Loading..."))
        self.progressBar = QProgressBar(self)
        self.progressBar.setMaximum(bytes)
        layout = QVBoxLayout()
        layout.addWidget(self.progressBar)
        self.setLayout(layout)

    def setReceivedSize(self, bytes):
        self.progressBar.setValue(bytes)

#
# Main application routine
#

def main():
    app = QApplication(sys.argv)
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
