"""Application main module."""

import logging
import signal
import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets

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

    def setRemoteTimeout(self, timeout: float) -> None:
        self.window.setRemoteTimeout(timeout)

    def loadDocument(self, filename: str) -> None:
        self.window.loadDocument(filename)

    def loadSettings(self) -> None:
        settings = QtCore.QSettings()
        # Window size
        size = settings.value("window/size", QtCore.QSize(800, 600))
        self.window.resize(size)

    def storeSettings(self) -> None:
        settings = QtCore.QSettings()
        # Window size
        size = self.window.size()
        settings.setValue("window/size", size)

    def eventLoop(self) -> None:
        timer = self.createInterruptTimer()
        timer.start(250)
        self.window.show()
        self.instance.exec_()
        timer.stop()
