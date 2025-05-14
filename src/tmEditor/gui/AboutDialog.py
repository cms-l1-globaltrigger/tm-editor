"""About dialog."""

import os
from typing import Optional

import markdown

from PyQt5 import QtCore, QtGui, QtWidgets

from tmEditor import __version__, tmeditor_rc
from tmGrammar import __version__ as utm_version

__all__ = ["AboutDialog"]

L1ApplicationAuthors = (
    (u"Bernhard Arnold", "bernhard.arnold@cern.ch"),
    (u"Herbert Bergauer", "herbert.bergauer@cern.ch"),
)
L1ApplicationContributors = (
    (u"Manfred Jeitler", "manfred.jeitler@cern.ch"),
    (u"Vasile Ghete", "vasile.mihai.ghete@cern.ch"),
)

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
        self.buttonBox.addButton(QtWidgets.QDialogButtonBox.Close)
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
        about = markdown.markdown("{}\n\nVersion **{}** (utm version {})".format(title, __version__, utm_version))
        self.aboutTextEdit.setText(about)
        changelog = markdown.markdown(self._readfile(":changelog"))
        self.changelogTextEdit.setHtml(changelog)
        self.authorsTextEdit.setText(self._userlist(L1ApplicationAuthors))
        self.thanksTextEdit.setText(self._userlist(L1ApplicationContributors))

    def _userlist(self, userlist, separator="<br />"):
        """Return HTML containing full name and email address of a user list tuple."""
        return separator.join(["{} &lt;{}&gt;".format(name, email) for name, email in userlist])

    def _readfile(self, filename: str) -> str:
        lines = []
        file = QtCore.QFile(filename)
        if not file.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            return ""
        istream = QtCore.QTextStream(file)
        while not istream.atEnd():
            lines.append(istream.readLine())
        return os.linesep.join(lines)
