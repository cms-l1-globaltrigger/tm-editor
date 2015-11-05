# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Open from URL dialog.

This dialog provides an URL entry to download an XML file from a remote location
using HTTP or FTP protocol.

Example usage:
>>> dialog = OpenUrlDialog()
>>> dialog.exec_()
>>> print dialog.url()
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import urllib2

__all__ = ['OpenUrlDialog', ]

class OpenUrlDialog(QDialog):
    """Dialog providing an URL input field."""

    def __init__(self, parent = None):
        super(OpenUrlDialog, self).__init__(parent)
        # Dialog appeareance
        self.setWindowTitle(self.tr("Open URL"))
        self.setMinimumWidth(500)
        # URL input
        self.urlLabel = QLabel(self.tr("Please enter a network URL:"), self)
        self.urlComboBox = QComboBox(self)
        self.urlComboBox.addItem("")
        self.urlComboBox.setEditable(True)
        self.urlComboBox.editTextChanged.connect(self.onUrlEdit)
        self.hintLabel = QLabel(self.tr("""
            <p style="color: #888; margin-left:5px;">
            http://www.example.com/sample.xml<br/>
            ftp://example.org/sample.xml
            </p>"""), self)
        # Button box
        buttonBox = QDialogButtonBox(QDialogButtonBox.Open | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.openButton = buttonBox.button(QDialogButtonBox.Open)
        self.openButton.setEnabled(False)
        # Create layout.
        gridLayout = QVBoxLayout()
        gridLayout.addWidget(self.urlLabel)
        gridLayout.addWidget(self.urlComboBox)
        gridLayout.addWidget(self.hintLabel)
        gridLayout.addWidget(buttonBox)
        self.setLayout(gridLayout)

    def onUrlEdit(self):
        self.openButton.setEnabled(len(self.url()))

    def url(self):
        """Returns current entered URL from combo box."""
        return str(self.urlComboBox.currentText())

    def loadRecentUrls(self):
        """Load recent URLs from application settings."""
        urls = QSettings().value("recent/urls").toStringList()
        self.urlComboBox.addItems(urls)

    def storeRecentUrls(self):
        """Store recent URLs including new entries in application settings."""
        urls = QStringList()
        urls.append(self.urlComboBox.currentText())
        for i in range(self.urlComboBox.count()):
            url = self.urlComboBox.itemText(i)
            if url and url not in urls:
                urls.append(url)
        QSettings().setValue("recent/urls", urls)
