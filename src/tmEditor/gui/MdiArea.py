"""Multi Document Interface (MDI) area."""

from typing import Optional

from PySide6 import QtCore, QtWidgets

from tmEditor.gui.CommonWidgets import createIcon
from tmEditor.gui.Document import Document

__all__ = ["MdiArea"]

# -----------------------------------------------------------------------------
#  MDI Area class
# -----------------------------------------------------------------------------

class MdiArea(QtWidgets.QTabWidget):
    """A tab widget based MDI area widget."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setContentsMargins(0, 0, 0, 0)
        # Close document by clicking on the tab close button.
        self.tabCloseRequested.connect(self.closeDocument)

    def documents(self) -> list[Document]:
        """Returns list containing all documents. Provided for convenience."""
        documents = []
        for index in range(self.count()):
            widget = self.widget(index)
            if isinstance(widget, Document):
                documents.append(widget)
        return documents

    def findDocument(self, filename) -> Optional[Document]:
        """Returns document if filename exists, else returns None."""
        result = list(filter(lambda document: document.filename() == filename, self.documents()))
        if result:
            return result[0]
        return None

    @QtCore.Slot(Document)
    def addDocument(self, document: Document) -> int:
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

    @QtCore.Slot()
    def currentDocument(self) -> Optional[Document]:
        """Returns current document. Provided for convenience."""
        widget = self.currentWidget()
        if isinstance(widget, Document):
            return widget
        return None

    @QtCore.Slot(int)
    def closeDocument(self, index: int) -> bool:
        """Close document and ask to save changes. Returns False if aborted."""
        if not self.count():
            return False
        document = self.widget(index)
        if isinstance(document, Document):
            if document.isModified():
                reply = QtWidgets.QMessageBox.warning(
                    self,
                    "Close document",
                    self.tr("The document \"{}\" has been modified.\n" \
                            "Do you want to save your changes or discard them?").format(document.name()),
                    QtWidgets.QMessageBox.StandardButton.Cancel |
                    QtWidgets.QMessageBox.StandardButton.Discard |
                    QtWidgets.QMessageBox.StandardButton.Save,
                    QtWidgets.QMessageBox.StandardButton.Cancel
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                    return False
                if reply == QtWidgets.QMessageBox.StandardButton.Save:
                    document.saveMenu()
        self.removeTab(index)
        return True

    @QtCore.Slot()
    def closeCurrentDocument(self) -> bool:
        """Close current document and ask to save changes. Provided for convenience."""
        return self.closeDocument(self.currentIndex())

    @QtCore.Slot()
    def documentModified(self) -> None:
        index = self.currentIndex()
        document = self.widget(index)
        if isinstance(document, Document):
            title = "*{}".format(document.name())  # Mark modified tabs with leading asterisk
            self.setTabText(index, title)
            self.currentChanged.emit(index)
