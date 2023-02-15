"""Multi Document Interface (MDI) area."""

from PyQt5 import QtCore, QtWidgets

from tmEditor.gui.CommonWidgets import createIcon

__all__ = ['MdiArea', ]

# -----------------------------------------------------------------------------
#  MDI Area class
# -----------------------------------------------------------------------------

class MdiArea(QtWidgets.QTabWidget):
    """A tab widget based MDI area widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setContentsMargins(0, 0, 0, 0)
        # Close document by clicking on the tab close button.
        self.tabCloseRequested.connect(self.closeDocument)

    def documents(self):
        """Returns list containing all documents. Provided for convenience."""
        return [self.widget(index) for index in range(self.count())]

    def findDocument(self, filename):
        """Returns document if filename exists, else returns None."""
        result = list(filter(lambda document: document.filename() == filename, self.documents()))
        if result:
            return result[0]
        return None

    @QtCore.pyqtSlot(str)
    def addDocument(self, document):
        """Adds document to MDI area. Prevents adding the same document twice.
        Returns index of tab of added document.
        """
        # Do no re-open a document, just raise its tab.
        duplicate = self.findDocument(document.filename())
        if duplicate:
            self.setCurrentWidget(duplicate)
            return self.currentIndex()
        document.modified.connect(self.documentModified)
        return self.addTab(document, createIcon("document"), document.name())

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
            reply = QtWidgets.QMessageBox.warning(
                self,
                "Close document",
                self.tr("The document \"{}\" has been modified.\n" \
                        "Do you want to save your changes or discard them?").format(document.name()),
                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Save,
                QtWidgets.QMessageBox.Cancel
            )
            if reply == QtWidgets.QMessageBox.Cancel:
                return False
            if reply == QtWidgets.QMessageBox.Save:
                document.saveMenu()
        self.removeTab(index)
        return True

    @QtCore.pyqtSlot()
    def closeCurrentDocument(self):
        """Close current document and ask to save changes. Provided for convenience."""
        return self.closeDocument(self.currentIndex())

    @QtCore.pyqtSlot()
    def documentModified(self):
        title = "*{0}".format(self.currentDocument().name()) # Mark modified tabs with leading asterisk
        self.setTabText(self.currentIndex(), title)
        self.currentChanged.emit(self.currentIndex())
