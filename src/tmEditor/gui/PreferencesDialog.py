"""Preferences dialog."""

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

__all__ = ["PreferencesDialog"]


class PreferencesDialog(QtWidgets.QDialog):
    """Preferences dialog providing settings for the application."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._setupUi()

    def _setupUi(self) -> None:
        self.setWindowTitle(self.tr("Preferences"))
        self.setWindowIcon(QtGui.QIcon(":icons/tm-editor.svg"))
        self.resize(240, 100)
        self.tabWidget = QtWidgets.QTabWidget(self)
        # Files tab
        self._createFilesTab()
        # Buttonbox
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.buttonBox.clicked.connect(self.close)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tabWidget)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

    def _createFilesTab(self) -> None:
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
        hbox.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))
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
        hbox.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))
        hbox.addWidget(self.clearHistoryButton)
        self.historyGroupBox.setLayout(hbox)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.recentGroupBox)
        vbox.addWidget(self.historyGroupBox)
        vbox.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))
        self.filesTab.setLayout(vbox)
        self.tabWidget.addTab(self.filesTab, self.tr("&Files"))

    @QtCore.Slot()
    def onClearRecent(self) -> None:
        """Clears history of recent files."""
        QtCore.QSettings().setValue("recent/files", [])

    @QtCore.Slot()
    def onClearHistory(self) -> None:
        """Clears history of downloaded URLs."""
        QtCore.QSettings().setValue("recent/urls", [])
