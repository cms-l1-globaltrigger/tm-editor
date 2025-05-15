"""About dialog."""

import os
from typing import Optional

import markdown

from PySide6 import QtCore, QtGui, QtWidgets

from tmEditor import tmeditor_rc
from tmEditor import __version__ as APP_VERSION
from tmGrammar import __version__ as UTM_VERSION

__all__ = ["AboutDialog"]


def readTextFile(filename: str) -> str:
    """Read text file from resources."""
    lines: list[str] = []
    file = QtCore.QFile(filename)
    if not file.open(QtCore.QIODevice.OpenModeFlag.ReadOnly | QtCore.QIODevice.OpenModeFlag.Text):
        return ""
    istream = QtCore.QTextStream(file)
    while not istream.atEnd():
        lines.append(istream.readLine())
    return os.linesep.join(lines)


class AboutDialog(QtWidgets.QDialog):
    """About dialog providing information on the application and credits."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        title: str = "Trigger Menu Editor"

        self.setWindowTitle(self.tr("About {}").format(title))
        self.setWindowIcon(QtGui.QIcon(":icons/tm-editor.svg"))
        self.setMinimumSize(420, 320)

        self.iconLabel: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self.iconLabel.setFixedSize(32, 32)
        self.iconLabel.setPixmap(QtGui.QPixmap(QtGui.QIcon(":icons/tm-editor.svg").pixmap(QtCore.QSize(32, 32))))

        self.titleLabel: QtWidgets.QLabel = QtWidgets.QLabel(self)

        self.aboutTextEdit: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.aboutTextEdit.setReadOnly(True)

        self.changelogTextEdit: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.changelogTextEdit.setReadOnly(True)

        self.authorsTextEdit: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.authorsTextEdit.setReadOnly(True)

        self.thanksTextEdit: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.thanksTextEdit.setReadOnly(True)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.addTab(self.aboutTextEdit, self.tr("&About"))
        self.tabs.addTab(self.changelogTextEdit, self.tr("&Changelog"))
        self.tabs.addTab(self.authorsTextEdit, self.tr("A&uthors"))
        self.tabs.addTab(self.thanksTextEdit, self.tr("&Thanks to"))

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.buttonBox.clicked.connect(self.close)


        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.iconLabel)
        hbox.addWidget(self.titleLabel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(hbox)
        layout.addWidget(self.tabs)
        layout.addWidget(self.buttonBox)

        # Initialize
        self.titleLabel.setText("<span style=\"font:bold 16px\">{}</span><br />{}".format(
            title,
            self.tr("Editor for CERN CMS Level-1 Trigger Menus.")
        ))
        about = markdown.markdown("{}\n\nVersion **{}** (utm version {})".format(title, APP_VERSION, UTM_VERSION))
        self.aboutTextEdit.setText(about)
        changelog = markdown.markdown(readTextFile(":changelog"))
        self.changelogTextEdit.setHtml(changelog)
        authors = readTextFile(":authors.txt")
        self.authorsTextEdit.setText(authors)
        contributors = readTextFile(":contributors.txt")
        self.thanksTextEdit.setText(contributors)
