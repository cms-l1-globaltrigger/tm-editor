"""Application main module."""

import logging
import signal
import sys

from PyQt5 import QtCore, QtWidgets

from .gui.MainWindow import MainWindow
from . import __version__

logger = logging.getLogger(__name__)


class Application:

    def __init__(self) -> None:
        self.instance = QtWidgets.QApplication(sys.argv)
        self.instance.setApplicationName("Trigger Menu Editor")
        self.instance.setApplicationDisplayName("L1-Trigger Menu Editor")
        self.instance.setApplicationVersion(__version__)
        self.instance.setOrganizationName("HEPHY")
        self.instance.setOrganizationDomain("hephy.at")

        self.registerSignalHandler()

        self.window = MainWindow()

    def registerSignalHandler(self) -> None:
        def signal_handler(signum, frame):
            if signum == signal.SIGINT:
                self.window.close()
        signal.signal(signal.SIGINT, signal_handler)

    def createInterruptTimer(self) -> QtCore.QTimer:
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: None)
        return timer

    def setRemoteTimeout(self, timeout: int) -> None:
        self.window.setRemoteTimeout(timeout)

    def loadDocument(self, filename: str) -> None:
        self.window.loadDocument(filename)

    def loadSettings(self) -> None:
        settings = QtCore.QSettings()
        # Window size
        geometry = settings.value("window/geometry", QtCore.QByteArray(), QtCore.QByteArray)
        if not self.window.restoreGeometry(geometry):
            self.window.resize(800, 600)
        state = settings.value("window/state", QtCore.QByteArray(), QtCore.QByteArray)
        self.window.restoreState(state)

    def storeSettings(self) -> None:
        settings = QtCore.QSettings()
        # Window size
        geometry = self.window.saveGeometry()
        settings.setValue("window/geometry", geometry)
        state = self.window.saveGeometry()
        settings.setValue("window/state", state)

    def eventLoop(self) -> None:
        timer = self.createInterruptTimer()
        timer.start(250)
        self.window.show()
        self.instance.exec_()
        timer.stop()
