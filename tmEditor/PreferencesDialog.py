# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Preferences dialog.
"""

from tmEditor.version import VERSION, PKG_RELEASE
from tmEditor import (
    Toolbox,
    tmeditor_rc,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['PreferencesDialog', ]

class PreferencesDialog(QDialog):
    """Preferences dialog providing settings for the application."""

    def __init__(self, parent=None):
        """Param title is the applciation name."""
        super(PreferencesDialog, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(self.tr("Preferences"))
        self.setWindowIcon(QIcon(':icons/tm-editor.svg'))
        self.resize(240, 180)
        vbox = QVBoxLayout()
        self.clearHistoryButton = QPushButton(self.tr("&Clear download history"), self)
        vbox.addWidget(self.clearHistoryButton)
        self.historyGroupBox = QGroupBox(self.tr("History"), self)
        self.historyGroupBox.setLayout(vbox)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.close)
        layout = QVBoxLayout()
        hbox = QHBoxLayout()
        layout.addWidget(self.historyGroupBox)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.clearHistoryButton.clicked.connect(self.onClearHistory)

    def onClearHistory(self):
        """Clears history of downloaded URLs."""
        QSettings().setValue("recent/urls", QStringList())
