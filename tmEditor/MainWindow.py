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
    Document,
    MdiArea,
    Toolbox,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import random
import webbrowser
import sys, os

__version__ = '0.1.0'
"""Applciation Version (edit this to increment the release version)."""

L1ContentsURL = "https://twiki.cern.ch/twiki/bin/viewauth/CMS/GlobalTriggerUpgradeL1T-uTme"

# NOTE: Bugfix for PyQt4.6
if not hasattr(QKeySequence, 'Quit'):
    QKeySequence.Quit = QKeySequence(Qt.CTRL + Qt.Key_Q)

# -----------------------------------------------------------------------------
#  Main window class
# -----------------------------------------------------------------------------

class MainWindow(QMainWindow):

    Version = __version__

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
        self.openAct.setIcon(Toolbox.createIcon("actions", "document-open"))
        self.openAct.triggered.connect(self.onOpen)
        # Action for saving the current file.
        self.saveAct = QAction(self.tr("&Save"), self)
        self.saveAct.setShortcut(QKeySequence.Save)
        self.saveAct.setStatusTip(self.tr("Save the current file"))
        self.saveAct.setIcon(Toolbox.createIcon("actions", "document-save"))
        self.saveAct.triggered.connect(self.onSave)
        # Action for saving the current file with a different name.
        self.saveAsAct = QAction(self.tr("&Save As..."), self)
        self.saveAsAct.setShortcut(QKeySequence.SaveAs)
        self.saveAsAct.setStatusTip(self.tr("Save the current file with a different name"))
        self.saveAsAct.setIcon(Toolbox.createIcon("actions", "document-save-as"))
        self.saveAsAct.triggered.connect(self.onSaveAs)
        # Action for closing the current file.
        self.closeAct = QAction(self.tr("&Close"), self)
        self.closeAct.setShortcut(QKeySequence.Close)
        self.closeAct.setStatusTip(self.tr("Close the current file"))
        self.closeAct.setIcon(Toolbox.createIcon("actions", "window-close"))
        self.closeAct.triggered.connect(self.onClose)
        # Action for quitting the program.
        self.quitAct = QAction(self.tr("&Quit"), self)
        self.quitAct.setShortcut(QKeySequence.Quit)
        self.quitAct.setStatusTip(self.tr("Quit the programm"))
        self.quitAct.setIcon(Toolbox.createIcon("actions", "application-exit"))
        self.quitAct.triggered.connect(self.close)
        # Open contents help URL.
        self.contentsAction = QAction(self.tr("&Contents"), self)
        self.contentsAction.setShortcut(QKeySequence(Qt.Key_F1))
        self.contentsAction.setStatusTip(self.tr("Open L1 Trigger Menu online manual"))
        self.contentsAction.setIcon(Toolbox.createIcon("actions", "help-about"))
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
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
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
        self.toolbar.addAction(self.saveAct)

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
        self.saveAct.setEnabled(enabled)
        self.saveAsAct.setEnabled(enabled)
        self.closeAct.setEnabled(enabled)

    def loadDocument(self, filename):
        """Load document from file and add it to the MDI area."""
        try:
            document = Document(filename, self)
        except RuntimeError, e:
            box = QMessageBox.critical(self,
                "Failed to open XML menu",
                str(e),
            )
        else:
            index = self.mdiArea.addDocument(document)
            self.mdiArea.setCurrentIndex(index)

    def onOpen(self):
        """Select a XML menu file using an dialog."""
        filenames = QFileDialog.getOpenFileNames(self, self.tr("Open files..."),
            os.getcwd(), "L1-Trigger Menus (*.xml)")
        for filename in filenames:
            self.loadDocument(str(filename))

    def onSave(self):
        document = self.mdiArea.currentDocument()
        try:
            document.saveMenu()
        except RuntimeError, e:
            box = QMessageBox.critical(self,
                "Failed to write XML menu",
                str(e),
            )

    def onSaveAs(self):
        filename = str(QFileDialog.getSaveFileName(self, self.tr("Save as..."),
            os.getcwd(), "L1-Trigger Menus (*.xml)"))
        if filename:
            document = self.mdiArea.currentDocument()
            try:
                document.saveMenu(filename)
                # TODO
                self.mdiArea.setTabText(self.mdiArea.currentIndex(), os.path.basename(filename))
            except RuntimeError, e:
                box = QMessageBox.critical(self,
                    "Failed to write XML menu",
                    str(e),
                )

    def onClose(self):
        index = self.mdiArea.currentIndex()
        self.mdiArea.closeDocument(index)

    def onShowContents(self):
        """Raise remote contents help."""
        webbrowser.open_new_tab(L1ContentsURL)

    def onShowAbout(self):
        """Raise about this application dialog."""
        dialog = AboutDialog(self.windowTitle(), self.Version, self)
        dialog.exec_()

    def closeEvent(self, event):
        """On window close event, close all open documents."""
        while self.mdiArea.count():
            if not self.mdiArea.closeCurrentDocument():
                event.ignore()
                return
        event.accept()

# -----------------------------------------------------------------------------
#  Main application routine
# -----------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    #app.setOrganizationName("HEPHY");
    #app.setApplicationName("L1TriggerMenuEditor");
    window = MainWindow()
    window.show()

    return app.exec_()

# -----------------------------------------------------------------------------
#  Application execution
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
