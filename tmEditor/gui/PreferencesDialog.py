# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Preferences dialog.
"""

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['PreferencesDialog', ]

# -----------------------------------------------------------------------------
#  Preferences dialog class
# -----------------------------------------------------------------------------

class PreferencesDialog(QtGui.QDialog):
    """Preferences dialog providing settings for the application."""

    def __init__(self, parent=None):
        super(PreferencesDialog, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(self.tr("Preferences"))
        self.setWindowIcon(QtGui.QIcon(':icons/tm-editor.svg'))
        self.resize(240, 100)
        hbox = QtGui.QHBoxLayout()
        self.clearHistoryButton = QtGui.QPushButton(self.tr("&Clear"), self)
        hbox.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        hbox.addWidget(self.clearHistoryButton)
        self.historyGroupBox = QtGui.QGroupBox(self.tr("Download history"), self)
        self.historyGroupBox.setLayout(hbox)
        self.verticalSpacer = QtGui.QSpacerItem(0, 0,
            QtGui.QSizePolicy.Minimum,
            QtGui.QSizePolicy.Expanding
        )
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.close)
        layout = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        layout.addWidget(self.historyGroupBox)
        layout.addItem(self.verticalSpacer)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.clearHistoryButton.clicked.connect(self.onClearHistory)

    def onClearHistory(self):
        """Clears history of downloaded URLs."""
        QtCore.QSettings().setValue("recent/urls", QtCore.QStringList())
