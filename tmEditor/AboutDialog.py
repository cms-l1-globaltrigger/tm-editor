# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""About dialog.
"""

from tmEditor import (
    Toolbox,
    tmeditor_rc,
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

__all__ = ['AboutDialog', ]

L1ApplicationAuthors = (
    (u"Bernhard Arnold", "bernhard.arnold@cern.ch"),
)
L1ApplicationContributors = (
    (u"Takashi Matsushita", "takashi.matsushita@cern.ch"),
    (u"Vasile Ghete", "vasile.mihai.ghete@cern.ch"),
)

class AboutDialog(QDialog):
    """About dialog providing information on the application and credits."""

    def __init__(self, title, version, parent = None):
        """Param title is the applciation name, version the main applications
        version."""
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("About %1").arg(title))
        self.setWindowIcon(QIcon(':icons/tm-editor.svg'))
        self.icon = QLabel(self)
        self.icon.setPixmap(QPixmap(QIcon(':icons/tm-editor.svg').pixmap(QSize(32, 32))))
        self.titleLabel = QLabel(self)
        self.aboutTextEdit = QTextEdit(self)
        self.aboutTextEdit.setReadOnly(True)
        self.authorsTextEdit = QTextEdit(self)
        self.authorsTextEdit.setReadOnly(True)
        self.thanksTextEdit  = QTextEdit(self)
        self.thanksTextEdit.setReadOnly(True)
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.aboutTextEdit, self.tr("&About"))
        self.tabs.addTab(self.authorsTextEdit, self.tr("A&uthors"))
        self.tabs.addTab(self.thanksTextEdit, self.tr("&Thanks to"))
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.close)
        layout = QVBoxLayout()
        hbox = QHBoxLayout()
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
        self.aboutTextEdit.setText(self.tr("%0<br /><br />Version %1").arg(title).arg(version))
        self.authorsTextEdit.setText(self._userlist(L1ApplicationAuthors))
        self.thanksTextEdit.setText(self._userlist(L1ApplicationContributors))

    def _userlist(self, userlist, separator = "<br />"):
        """Return HTML containing full name and email address of a user list tuple."""
        return separator.join(["{0} &lt;{1}&gt;".format(name, email) for name, email in userlist])
