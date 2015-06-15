#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Main window class holding a MDI area.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import random
import sys, os

# -----------------------------------------------------------------------------
#  Helpers
# -----------------------------------------------------------------------------

def createIcon(category, name):
    """Factory function, creates a multi resolution gnome theme icon."""
    icon = QIcon()
    for size in 16, 24, 32, 64, 128:
        icon.addFile("/usr/share/icons/gnome/{size}x{size}/{category}/{name}.png".format(**locals()))
    return icon

# -----------------------------------------------------------------------------
#  Main window
# -----------------------------------------------------------------------------

class MainWindow(QMainWindow):

    ApplicationTitle = "L1-Trigger Menu Editor"

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        # Setup window.
        self.setWindowIcon(createIcon("apps", "text-editor"))
        self.setWindowTitle(self.ApplicationTitle)
        self.resize(800, 600)
        # Create actions and toolbars.
        self.createActions()
        self.createToolbar()
        self.createStatusBar()
        # Create MDI area
        self.mdiArea = MdiArea()
        self.mdiArea.currentChanged.connect(self.updateStatusBar)
        self.setCentralWidget(self.mdiArea)

        #d = Document("L1Menu_Sample")
        #d.algorithms = 6
        #d.cuts = 1
        #d.objects = 7
        #self.mdiArea.addDocument(d)
        #d = Document("L1Menu_MuonsCastor")
        #d.algorithms = 42
        #d.cuts = 13
        #d.objects = 124
        #self.mdiArea.addDocument(d)
        # Initialize
        self.updateStatusBar()

    def createActions(self):
        # Action for opening a new connections file.
        self.openAct = QAction("&Open...", self)
        self.openAct.setShortcut(QKeySequence.Open)
        self.openAct.setStatusTip("Open an existing file")
        self.openAct.setIcon(createIcon("actions", "document-open"))
        self.openAct.triggered.connect(self.fileOpen)

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
        self.statusAlgorithms.setText(QString(" Algorithms: %1 ").arg(document.algorithms if document else '--'))
        self.statusCuts.setText(QString(" Cuts: %1 ").arg(document.cuts if document else '--'))
        self.statusObjects.setText(QString(" Objects: %1 ").arg(document.objects if document else '--'))
        self.statusBar().showMessage("Ready")

    def fileOpen(self):
        """Select a connections file using a file open dialog."""
        filename = str(QFileDialog.getOpenFileName(self, "Open connection file",
            os.getcwd(), "L1-Trigger Menus (*.xml)"))
        if not filename:
            return
        document = Document(os.path.basename(filename))
        document.algorithms = random.randint(0,512)
        document.cuts = random.randint(0,512)
        document.objects = random.randint(0,512)
        index = self.mdiArea.addDocument(document)
        self.mdiArea.setCurrentIndex(index)

# -----------------------------------------------------------------------------
#  Multi Document Interface (MDI) area
# -----------------------------------------------------------------------------

class MdiArea(QTabWidget):
    """A tab widget based MDI area widget."""

    def __init__(self, parent = None):
        super(MdiArea, self).__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setContentsMargins(0, 0, 0, 0)
        # Close document by clicking on the tab close button.
        self.tabCloseRequested.connect(self.removeDocument)

    def addDocument(self, document):
        return self.addTab(document, createIcon("mimetypes", "document"), document.name)

    def currentDocument(self):
        return self.currentWidget()

    def removeDocument(self, index):
        """Close document and ask to save changes."""
        document = self.widget(index)
        reply = QMessageBox.warning(self, "Close document",
            QString("The document \"%1\" has been modified.\n" \
                    "Do you want to save your changes or discard them?").arg(document.name),
            QMessageBox.Cancel | QMessageBox.Discard | QMessageBox.Save, QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return False
        if reply == QMessageBox.Save:
            pass # save
        self.removeTab(index)

# -----------------------------------------------------------------------------
#  Document widget
# -----------------------------------------------------------------------------

class Document(QWidget):

    def __init__(self, name, parent = None):
        super(Document, self).__init__(parent)
        self.name = name
        self.setContentsMargins(0, 0, 0, 0)
        self.contentTreeWidget = QTreeWidget(self)
        self.contentTreeWidget.setObjectName("T")
        self.contentTreeWidget.setStyleSheet("#T { background: #eee; }")
        item = QTreeWidgetItem(self.contentTreeWidget,[name])
        QTreeWidgetItem(item, ["Algorithms"])
        QTreeWidgetItem(item, ["Cuts"])
        QTreeWidgetItem(item, ["Objects"])
        self.contentTreeWidget.expandAll()
        self.itemsTableView = QTableView(self)
        self.setStyleSheet("border: 0;")
        self.itemPreview = QTextEdit(self)
        self.itemPreview.setObjectName("P")
        self.itemPreview.setStyleSheet("#P { background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(205, 205, 255, 255), stop:1 rgba(255, 255, 255, 255));; }")
        self.vsplitter = SlimSplitter(Qt.Horizontal, self)
        self.vsplitter.setObjectName("A")
        self.vsplitter.setStyleSheet("#A { background: #888; }")
        self.vsplitter.addWidget(self.contentTreeWidget)
        self.vsplitter.setOpaqueResize(False)
        self.hsplitter = SlimSplitter(Qt.Vertical, self)
        self.hsplitter.addWidget(self.itemsTableView)
        self.hsplitter.addWidget(self.itemPreview)
        self.vsplitter.addWidget(self.hsplitter)
        self.vsplitter.setStretchFactor(0, 0)
        self.vsplitter.setStretchFactor(1, 1)
        self.vsplitter.setSizes([200, 600])
        layout = QVBoxLayout()
        layout.addWidget(self.vsplitter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

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
