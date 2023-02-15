"""Preferences dialog."""

from PyQt5 import QtCore, QtGui, QtWidgets

__all__ = ['PreferencesDialog', ]

# -----------------------------------------------------------------------------
#  Preferences dialog class
# -----------------------------------------------------------------------------

class PreferencesDialog(QtWidgets.QDialog):
    """Preferences dialog providing settings for the application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(self.tr("Preferences"))
        self.setWindowIcon(QtGui.QIcon(':icons/tm-editor.svg'))
        self.resize(240, 100)
        self.tabWidget = QtWidgets.QTabWidget(self)
        # Files tab
        self.createFilesTab()
        # Buttonbox
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.close)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tabWidget)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

    def createFilesTab(self):
        # Page
        self.filesTab = QtWidgets.QWidget(self)
        # Recent files group box
        self.recentGroupBox = QtWidgets.QGroupBox(self.tr("&Recent files"), self)
        # Clear button
        self.clearRecentButton = QtWidgets.QPushButton(self.tr("C&lear"), self)
        self.clearRecentButton.setAutoDefault(False)
        self.clearRecentButton.clicked.connect(self.onClearRecent)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel(self.tr("Clear recent files history"), self))
        hbox.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        hbox.addWidget(self.clearRecentButton)
        self.recentGroupBox.setLayout(hbox)
        # Download histry group box
        self.historyGroupBox = QtWidgets.QGroupBox(self.tr("&Download history"), self)
        # Clear button
        self.clearHistoryButton = QtWidgets.QPushButton(self.tr("Cl&ear"), self)
        self.clearHistoryButton.setAutoDefault(False)
        self.clearHistoryButton.clicked.connect(self.onClearHistory)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel(self.tr("Clear URLs from download history"), self))
        hbox.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        hbox.addWidget(self.clearHistoryButton)
        self.historyGroupBox.setLayout(hbox)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.recentGroupBox)
        vbox.addWidget(self.historyGroupBox)
        vbox.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))
        self.filesTab.setLayout(vbox)
        self.tabWidget.addTab(self.filesTab, self.tr("&Files"))

    def onClearRecent(self):
        """Clears history of recent files."""
        QtCore.QSettings().setValue("recent/files", [])

    def onClearHistory(self):
        """Clears history of downloaded URLs."""
        QtCore.QSettings().setValue("recent/urls", [])
