"""External signal editor dialog."""

from typing import Optional

from PySide6 import QtWidgets

from tmEditor.core.Algorithm import toExternal
from tmEditor.core.AlgorithmHelper import AlgorithmHelper
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter

# Common widgets
from tmEditor.gui.CommonWidgets import PrefixedSpinBox, createIcon, miniIcon

__all__ = ["ExtSignalEditorDialog"]

kEXT = "EXT"
kName = "name"
kSystem = "system"
kCable = "cable"
kChannel = "channel"
kLabel = "label"


class ExtSignalEditorDialog(QtWidgets.QDialog):
    """External signal editor dialog class."""

    def __init__(self, menu, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """Constructor, takes a reference to a menu and an optional parent."""
        super().__init__(parent)
        self.menu = menu
        self._setupUi()
        # Connect signals
        self.signalComboBox.currentIndexChanged.connect(self.updateInfoText)
        self.offsetSpinBox.valueChanged.connect(self.updateInfoText)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # Initialize
        self.updateInfoText()

    def _setupUi(self) -> None:
        self.setWindowIcon(createIcon("wizard-ext-signal"))
        self.setWindowTitle(self.tr("External Signal Editor"))
        self.resize(640, 280)
        self.signalLabel = QtWidgets.QLabel(self.tr("Signal"), self)
        self.signalLabel.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.signalComboBox = QtWidgets.QComboBox(self)
        self.signalComboBox.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        for signal in self.menu.extSignals.extSignals:
            self.signalComboBox.addItem(miniIcon("ext"), "_".join((kEXT, signal[kName])))
        self.offsetSpinBox = PrefixedSpinBox(self)
        self.offsetSpinBox.setRange(-2, 2)
        self.offsetSpinBox.setValue(0)
        self.offsetSpinBox.setSuffix(self.tr(" BX"))
        self.infoTextEdit = QtWidgets.QTextEdit(self)
        self.infoTextEdit.setReadOnly(True)
        self.infoTextEdit.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.signalLabel, 0, 0)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.signalComboBox)
        hbox.addWidget(self.offsetSpinBox)
        layout.addLayout(hbox, 0, 1)
        layout.addWidget(self.infoTextEdit, 0, 2, 3, 1)
        layout.addWidget(self.buttonBox, 3, 0, 1, 3)
        self.setLayout(layout)

    def name(self) -> str:
        """Returns external signal name."""
        return self.signalComboBox.currentText()

    def bxOffset(self) -> int:
        return self.offsetSpinBox.value()

    def expression(self) -> str:
        """Returns object expression selected by the inputs."""
        expression = AlgorithmHelper()
        expression.addExtSignal(
            name=self.name(),
            bx_offset=self.bxOffset(),
        )
        return AlgorithmFormatter.normalize(expression.serialize())

    def updateInfoText(self) -> None:
        """Update info box text."""
        name = toExternal(self.name()).signal_name
        for signal in filter(lambda signal: signal[kName] == name, self.menu.extSignals.extSignals):
            system = signal[kSystem]
            cable = signal[kCable]
            channel = signal[kChannel]
            label = signal[kLabel] if kLabel in signal else ""
            expression = self.expression()
            text = []
            text.append(f"<h3>External Signal Requirement</h3>")
            text.append(f"<p>System: {system}</p>")
            text.append(f"<p>Cable: {cable}</p>")
            text.append(f"<p>Channel: {channel}</p>")
            if label:
                text.append(f"<p>Label: {label}</p>")
            text.append(f"<h4>Preview</h4>")
            text.append(f"<p><pre>{expression}</pre></p>")
            self.infoTextEdit.setText("".join(text))
            break

    def loadExtSignal(self, token) -> None:
        """Load dialog by values from external signal. Will raise a ValueError if string
        *token* is not a valid external signal.
        """
        signal = toExternal(token)
        self.signalComboBox.setCurrentIndex(self.signalComboBox.findText(signal.basename))
        self.offsetSpinBox.setValue(signal.bx_offset)
