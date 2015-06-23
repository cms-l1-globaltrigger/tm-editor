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
    Document,
    MdiArea,
    Toolbox,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import random
import sys, os

class MainWindow(QMainWindow):

    ApplicationTitle = "L1-Trigger Menu Editor"

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        # Setup window.
        self.setWindowIcon(Toolbox.createIcon("apps", "text-editor"))
        self.setWindowTitle(self.ApplicationTitle)
        self.resize(800, 600)
        # Create actions and toolbars.
        self.createActions()
        self.createMenus()
        self.createToolbar()
        self.createStatusBar()
        # Create MDI area
        self.mdiArea = MdiArea()
        self.mdiArea.currentChanged.connect(self.updateStatusBar)
        self.setCentralWidget(self.mdiArea)
        # Initialize
        self.updateStatusBar()

    def createActions(self):
        # Action for opening a new connections file.
        self.openAct = QAction(self.tr("&Open..."), self)
        self.openAct.setShortcut(QKeySequence.Open)
        self.openAct.setStatusTip(self.tr("Open an existing file"))
        self.openAct.setIcon(Toolbox.createIcon("actions", "document-open"))
        self.openAct.triggered.connect(self.onFileOpen)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.openAct)
        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))

    def createToolbar(self):
        """Create main toolbar and pin to top area."""
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.addAction(self.openAct)

    def createStatusBar(self):
        """Create status bar and populate with status labels."""
        self.statusBar()
        self.statusAlgorithms = QLabel()
        self.statusCuts = QLabel()
        self.statusObjects = QLabel()
        self.statusBar().addPermanentWidget(self.statusAlgorithms)
        self.statusBar().addPermanentWidget(self.statusCuts)
        self.statusBar().addPermanentWidget(self.statusObjects)

    def createStatusBarLabel(self):
        """Create labels for status bar."""
        label = QLabel(self)
        label.setFrameShadow(QFrame.Sunken)
        label.setFrameShape(QFrame.Panel)
        return label

    def updateStatusBar(self, index = None):
        """Update status bar labels."""
        document = self.mdiArea.currentDocument()
        self.statusAlgorithms.setText(QString(" Algorithms: %1 ").arg(len(document.menu.algorithms) if document else '--'))
        self.statusCuts.setText(QString(" Cuts: %1 ").arg(len(document.menu.cuts) if document else '--'))
        self.statusObjects.setText(QString(" Objects: %1 ").arg(len(document.menu.objects) if document else '--'))
        self.statusBar().showMessage("Ready")

    def loadDocument(self, filename):
        document = Document(os.path.basename(filename))
        index = self.mdiArea.addDocument(document)
        self.mdiArea.setCurrentIndex(index)

    def onFileOpen(self):
        """Select a XML menu file using an dialog."""
        filename = str(QFileDialog.getOpenFileName(self, "Open connection file",
            os.getcwd(), "L1-Trigger Menus (*.xml)"))
        if not filename:
            return
        self.loadDocument(filename)

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
