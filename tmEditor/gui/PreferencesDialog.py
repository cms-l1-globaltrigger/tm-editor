# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Preferences dialog.
"""

from tmEditor.PyQt5Proxy import QtCore
from tmEditor.PyQt5Proxy import QtGui
from tmEditor.PyQt5Proxy import QtWidgets

__all__ = ['PreferencesDialog', ]

# -----------------------------------------------------------------------------
#  Preferences dialog class
# -----------------------------------------------------------------------------

class PreferencesDialog(QtWidgets.QDialog):
    """Preferences dialog providing settings for the application."""

    def __init__(self, parent=None):
        super(PreferencesDialog, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(self.tr("Preferences"))
        self.setWindowIcon(QtGui.QIcon(':icons/tm-editor.svg'))
        self.resize(240, 100)
        hbox = QtWidgets.QHBoxLayout()
        self.clearHistoryButton = QtWidgets.QPushButton(self.tr("&Clear"), self)
        hbox.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        hbox.addWidget(self.clearHistoryButton)
        self.historyGroupBox = QtWidgets.QGroupBox(self.tr("Download history"), self)
        self.historyGroupBox.setLayout(hbox)
        self.verticalSpacer = QtWidgets.QSpacerItem(0, 0,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.close)
        layout = QtWidgets.QVBoxLayout()
        hbox = QtWidgets.QHBoxLayout()
        layout.addWidget(self.historyGroupBox)
        layout.addItem(self.verticalSpacer)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.clearHistoryButton.clicked.connect(self.onClearHistory)

    def onClearHistory(self):
        """Clears history of downloaded URLs."""
        QtCore.QSettings().setValue("recent/urls", [])
