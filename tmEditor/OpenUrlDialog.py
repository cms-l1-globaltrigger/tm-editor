# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Open from URL dialog.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import urllib2

__all__ = ['OpenUrlDialog', ]

class OpenUrlDialog(QDialog):

    def __init__(self, parent = None):
        super(OpenUrlDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Open URL"))
        self.resize(500, 200)
        # URL input
        self.urlLabel = QLabel(self.tr("Please enter a network URL:"), self)
        self.urlComboBox = QComboBox(self)
        urls = QSettings().value("recent/urls").toStringList()
        self.urlComboBox.addItem("")
        self.urlComboBox.addItems(urls)
        self.urlComboBox.setEditable(True)
        self.hintLabel = QLabel(self.tr(
            "<span style=\"color: #888;\">"
            "http://www.example.com/sample.xml<br/>"
            "ftp://example.org/sample.xml"
            "</span>"), self)
        # Button box
        buttonBox = QDialogButtonBox(QDialogButtonBox.Open | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        # Create layout.
        gridLayout = QVBoxLayout()
        gridLayout.addWidget(self.urlLabel)
        gridLayout.addWidget(self.urlComboBox)
        gridLayout.addWidget(self.hintLabel)
        gridLayout.addWidget(buttonBox)
        self.setLayout(gridLayout)

    def accept(self):
        urls = QStringList() # Strip empty entries.
        for i in range(self.urlComboBox.count()):
            url = self.urlComboBox.itemText(i)
            if url and url not in urls:
                urls.append(url)
        QSettings().setValue("recent/urls", urls)
        super(OpenUrlDialog, self).accept()

    def url(self):
        return str(self.urlComboBox.currentText())
