"""About dialog.
"""
import sys, os
import markdown

from PyQt5 import QtCore, QtGui, QtWidgets

from tmEditor import __version__
from tmEditor.core import toolbox
from tmEditor import tmeditor_rc

__all__ = ['AboutDialog', ]

L1ApplicationAuthors = (
    (u"Bernhard Arnold", "bernhard.arnold@cern.ch"),
)
L1ApplicationContributors = (
    (u"Manfred Jeitler", "manfred.jeitler@cern.ch"),
    (u"Vasile Ghete", "vasile.mihai.ghete@cern.ch"),
)

class AboutDialog(QtWidgets.QDialog):
    """About dialog providing information on the application and credits."""

    def __init__(self, title, parent=None):
        """Param title is the applciation name."""
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("About {}").format(title))
        self.setWindowIcon(QtGui.QIcon(':icons/tm-editor.svg'))
        self.icon = QtWidgets.QLabel(self)
        self.icon.setFixedSize(32, 32)
        self.icon.setPixmap(QtGui.QPixmap(QtGui.QIcon(':icons/tm-editor.svg').pixmap(QtCore.QSize(32, 32))))
        self.titleLabel = QtWidgets.QLabel(self)
        self.aboutTextEdit = QtWidgets.QTextEdit(self)
        self.aboutTextEdit.setReadOnly(True)
        self.changelogTextEdit = QtWidgets.QTextEdit(self)
        self.changelogTextEdit.setReadOnly(True)
        self.authorsTextEdit = QtWidgets.QTextEdit(self)
        self.authorsTextEdit.setReadOnly(True)
        self.thanksTextEdit  = QtWidgets.QTextEdit(self)
        self.thanksTextEdit.setReadOnly(True)
        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.addTab(self.aboutTextEdit, self.tr("&About"))
        self.tabs.addTab(self.changelogTextEdit, self.tr("&Changelog"))
        self.tabs.addTab(self.authorsTextEdit, self.tr("A&uthors"))
        self.tabs.addTab(self.thanksTextEdit, self.tr("&Thanks to"))
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.close)
        layout = QtWidgets.QVBoxLayout()
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.icon)
        hbox.addWidget(self.titleLabel)
        layout.addLayout(hbox)
        layout.addWidget(self.tabs)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        # Initialize
        self.titleLabel.setText('<span style="font:bold 16px">{}</span><br />{}'.format(
            title,
            self.tr("Editor for CERN CMS Level-1 Trigger Menus."))
        )
        about = markdown.markdown("{}\n\nVersion **{}**".format(title, __version__))
        self.aboutTextEdit.setText(about)
        changelog = markdown.markdown(self._readfile(":changelog"))
        self.changelogTextEdit.setText(changelog)
        self.authorsTextEdit.setText(self._userlist(L1ApplicationAuthors))
        self.thanksTextEdit.setText(self._userlist(L1ApplicationContributors))

    def _userlist(self, userlist, separator = "<br />"):
        """Return HTML containing full name and email address of a user list tuple."""
        return separator.join(["{} &lt;{}&gt;".format(name, email) for name, email in userlist])

    def _readfile(self, filename):
        lines = []
        file = QtCore.QFile(filename)
        if not file.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            return ''
        istream = QtCore.QTextStream(file)
        while not istream.atEnd():
           lines.append(istream.readLine())
        return os.linesep.join(lines)
