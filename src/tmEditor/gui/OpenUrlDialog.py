"""Open from URL dialog.

This dialog provides an URL entry to download an XML file from a remote location
using HTTP or FTP protocol.

Example usage:
>>> dialog = OpenUrlDialog()
>>> dialog.exec_()
>>> print dialog.url()
"""

from typing import Optional

from PySide6 import QtCore, QtWidgets

__all__ = ["OpenUrlDialog"]


class OpenUrlDialog(QtWidgets.QDialog):
    """Dialog providing an URL input field."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        # Dialog appeareance
        self.setWindowTitle(self.tr("Open URL"))
        self.setMinimumWidth(500)
        # URL input
        self.urlLabel = QtWidgets.QLabel(self.tr("Please enter a network URL:"), self)
        self.urlComboBox = QtWidgets.QComboBox(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
        self.urlComboBox.setSizePolicy(sizePolicy)
        self.urlComboBox.addItem("")
        self.urlComboBox.setEditable(True)
        self.urlComboBox.editTextChanged.connect(self.onUrlEdit)
        self.hintLabel = QtWidgets.QLabel(self.tr("""
            <p style="color: #888; margin-left:5px;">
            http://www.example.com/sample.xml<br/>
            ftp://example.org/sample.xml
            </p>"""), self)
        # Button box
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Open |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.openButton = buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Open)
        self.openButton.setEnabled(False)
        # Create layout.
        gridLayout = QtWidgets.QVBoxLayout()
        gridLayout.addWidget(self.urlLabel)
        gridLayout.addWidget(self.urlComboBox)
        gridLayout.addWidget(self.hintLabel)
        gridLayout.addWidget(buttonBox)
        self.setLayout(gridLayout)

    def onUrlEdit(self) -> None:
        self.openButton.setEnabled(len(self.url()) != 0)

    def url(self) -> str:
        """Returns current entered URL from combo box."""
        return self.urlComboBox.currentText()

    def loadRecentUrls(self) -> None:
        """Load recent URLs from application settings."""
        urls = QtCore.QSettings().value("recent/urls") or []
        if isinstance(urls, list):
            self.urlComboBox.addItems(urls)

    def storeRecentUrls(self) -> None:
        """Store recent URLs including new entries in application settings."""
        urls = []
        urls.append(self.urlComboBox.currentText())
        for i in range(self.urlComboBox.count()):
            url = self.urlComboBox.itemText(i)
            if url and url not in urls:
                urls.append(url)
        QtCore.QSettings().setValue("recent/urls", urls)
