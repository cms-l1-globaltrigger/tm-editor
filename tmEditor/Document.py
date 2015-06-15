# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Document widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Document(QWidget):
    """Document container widget used by MDI area."""

    def __init__(self, name, parent = None):
        super(Document, self).__init__(parent)
        self.setName(name)
        self.setModified(False)
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

    def setName(self, name):
        self._name = name

    def name(self):
        return self._name

    def isModified(self):
        return self._isModified

    def setModified(self, modified):
        self._isModified = modified

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
