# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Multi Document Interface (MDI) area.
"""

from tmEditor import Document
from tmEditor import Toolbox

from PyQt4 import QtCore
from PyQt4 import QtGui

class MdiArea(QtGui.QTabWidget):
    """A tab widget based MDI area widget."""

    def __init__(self, parent = None):
        super(MdiArea, self).__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setContentsMargins(0, 0, 0, 0)
        # Close document by clicking on the tab close button.
        self.tabCloseRequested.connect(self.closeDocument)

    def documents(self):
        """Returns list containing all documents. Provided for convenience."""
        return [self.widget(index) for index in range(self.count())]

    @QtCore.pyqtSlot(str)
    def addDocument(self, document):
        """Adds document to MDI area. Prevents adding the same document twice.
        Returns index of tab of added document.
        """
        # Do no re-open a document, just raise its tab.
        result = filter(lambda doc: document.filename() == doc.filename(), self.documents())
        if result:
            self.setCurrentWidget(result[0])
            return self.currentIndex()
        document.modified.connect(self.documentChanged)
        return self.addTab(document, Toolbox.createIcon("document"), document.name())

    @QtCore.pyqtSlot()
    def currentDocument(self):
        """Returns current document. Provided for convenience."""
        return self.currentWidget()

    @QtCore.pyqtSlot(int)
    def closeDocument(self, index):
        """Close document and ask to save changes. Returns False if aborted."""
        if not self.count():
            return False
        document = self.widget(index)
        if document.isModified():
            reply = QtGui.QMessageBox.warning(self, "Close document",
                QtCore.QString("The document \"%1\" has been modified.\n" \
                        "Do you want to save your changes or discard them?").arg(document.name()),
                QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Save,
                QtGui.QMessageBox.Cancel)
            if reply == QtGui.QMessageBox.Cancel:
                return False
            if reply == QtGui.QMessageBox.Save:
                document.saveMenu()
        self.removeTab(index)
        return True

    @QtCore.pyqtSlot()
    def closeCurrentDocument(self):
        """Close current document and ask to save changes. Provided for convenience."""
        return self.closeDocument(self.currentIndex())

    @QtCore.pyqtSlot()
    def documentChanged(self):
        self.currentChanged.emit(self.currentIndex())
