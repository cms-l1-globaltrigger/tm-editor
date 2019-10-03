# -*- coding: utf-8 -*-

"""About dialog.
"""

from tmEditor import __version__
from tmEditor.core import toolbox
from tmEditor import tmeditor_rc

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sys

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
        self.setWindowTitle(self.tr("About {0}").format(title))
        self.setWindowIcon(QtGui.QIcon(':icons/tm-editor.svg'))
        self.icon = QtWidgets.QLabel(self)
        self.icon.setPixmap(QtGui.QPixmap(QtGui.QIcon(':icons/tm-editor.svg').pixmap(QtCore.QSize(32, 32))))
        self.titleLabel = QtWidgets.QLabel(self)
        self.aboutTextEdit = QtWidgets.QTextEdit(self)
        self.aboutTextEdit.setReadOnly(True)
        self.environTextEdit = QtWidgets.QTextEdit(self)
        self.environTextEdit.setReadOnly(True)
        self.changelogTextEdit = QtWidgets.QTextEdit(self)
        self.changelogTextEdit.setReadOnly(True)
        self.authorsTextEdit = QtWidgets.QTextEdit(self)
        self.authorsTextEdit.setReadOnly(True)
        self.thanksTextEdit  = QtWidgets.QTextEdit(self)
        self.thanksTextEdit.setReadOnly(True)
        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.addTab(self.aboutTextEdit, self.tr("&About"))
        self.tabs.addTab(self.environTextEdit, self.tr("&Environment"))
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
        self.titleLabel.setText('<span style="font:bold 16px">{0}</span><br />{1}'.format(
            self.tr("{0}").format(title),
            self.tr("Graphical editor for L1-Trigger Menus for the CERN CMS L1-Global Trigger."))
        )
        pythonVersion = "Python version {0}.{1}.{2}-{3}{4}".format(*sys.version_info)
        pyqtVersion = "PyQt5 version {1}".format(QtCore.QT_VERSION_STR)
        rootDir = toolbox.getRootDir()
        xsdDir = toolbox.getXsdDir()
        self.aboutTextEdit.setText(self.tr("{0}<br /><br />Version <strong>{1}-{2}</strong>").format(title, __version__, ))
        self.environTextEdit.setText(self.tr("{0}<br />{1}<br />UTM_ROOT={2}<br />UTM_XSD_DIR={3}").format(pythonVersion, pyqtVersion, rootDir, xsdDir))
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
           lines.append(istream.readLine())
        return "\n".join(lines)
