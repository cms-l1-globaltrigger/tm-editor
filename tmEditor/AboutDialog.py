# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""About dialog.
"""

from tmEditor.version import VERSION, PKG_RELEASE
from tmEditor import Toolbox
from tmEditor import tmeditor_rc

from PyQt4 import QtCore
from PyQt4 import QtGui

__all__ = ['AboutDialog', ]

L1ApplicationAuthors = (
    (u"Bernhard Arnold", "bernhard.arnold@cern.ch"),
)
L1ApplicationContributors = (
    (u"Takashi Matsushita", "takashi.matsushita@cern.ch"),
    (u"Vasile Ghete", "vasile.mihai.ghete@cern.ch"),
)

class AboutDialog(QtGui.QDialog):
    """About dialog providing information on the application and credits."""

    def __init__(self, title, parent=None):
        """Param title is the applciation name."""
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("About %1").arg(title))
        self.setWindowIcon(QtGui.QIcon(':icons/tm-editor.svg'))
        self.icon = QtGui.QLabel(self)
        self.icon.setPixmap(QtGui.QPixmap(QtGui.QIcon(':icons/tm-editor.svg').pixmap(QtCore.QSize(32, 32))))
        self.titleLabel = QtGui.QLabel(self)
        self.aboutTextEdit = QtGui.QTextEdit(self)
        self.aboutTextEdit.setReadOnly(True)
        self.changelogTextEdit = QtGui.QTextEdit(self)
        self.changelogTextEdit.setReadOnly(True)
        self.authorsTextEdit = QtGui.QTextEdit(self)
        self.authorsTextEdit.setReadOnly(True)
        self.thanksTextEdit  = QtGui.QTextEdit(self)
        self.thanksTextEdit.setReadOnly(True)
        self.tabs = QtGui.QTabWidget(self)
        self.tabs.addTab(self.aboutTextEdit, self.tr("&About"))
        self.tabs.addTab(self.changelogTextEdit, self.tr("&Changelog"))
        self.tabs.addTab(self.authorsTextEdit, self.tr("A&uthors"))
        self.tabs.addTab(self.thanksTextEdit, self.tr("&Thanks to"))
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.close)
        layout = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.icon)
        hbox.addWidget(self.titleLabel)
        layout.addLayout(hbox)
        layout.addWidget(self.tabs)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        # Initialize
        self.titleLabel.setText('<span style="font:bold 16px">{0}</span><br/>{1}'.format(
            self.tr("%0").arg(title),
            self.tr("Graphical editor for L1-Trigger Menus for the CERN CMS L1-Global Trigger."))
        )
        self.aboutTextEdit.setText(self.tr("%0<br /><br />Version %1-%2").arg(title).arg(VERSION).arg(PKG_RELEASE))
        self.changelogTextEdit.setText(self._readfile(":changelog"))
        self.authorsTextEdit.setText(self._userlist(L1ApplicationAuthors))
        self.thanksTextEdit.setText(self._userlist(L1ApplicationContributors))

    def _userlist(self, userlist, separator = "<br />"):
        """Return HTML containing full name and email address of a user list tuple."""
        return separator.join(["{0} &lt;{1}&gt;".format(name, email) for name, email in userlist])

    def _readfile(self, filename):
        lines = []
        file = QtCore.QFile(filename)
        if not file.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            return ''
        istream = QtCore.QTextStream(file)
        while not istream.atEnd():
           lines.append(str(istream.readLine()))
        return "\n".join(lines)
