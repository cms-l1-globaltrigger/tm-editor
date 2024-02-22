"""Cut editor dialog."""

import math
import logging
import re
from typing import List, Optional, Tuple

from PyQt5 import QtCore, QtGui, QtWidgets

import tmGrammar

from tmEditor.core.types import FunctionCutTypes
from tmEditor.core.Algorithm import Cut
from tmEditor.core import toolbox

from tmEditor.core.Algorithm import (
    calculateDRRange,
    calculateInvMassRange,
    calculateTwoBodyPtRange
)

from tmEditor.gui.CommonWidgets import (
    RestrictedLineEdit,
    RestrictedPlainTextEdit,
    EtaCutChart,
    PhiCutChart
)

__all__ = ["CutEditorDialog"]

RangeType = Tuple[float, float]

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kComment: str = "comment"
kData: str = "data"
kMaximum: str = "maximum"
kMinimum: str = "minimum"
kName: str = "name"
kNBits: str = "n_bits"
kNumber: str = "number"
kType: str = "type"
kObject: str = "object"

ObjectCollectionRanges = {
    tmGrammar.MU: (0, 7),
    tmGrammar.EG: (0, 11),
    tmGrammar.JET:  (0, 11),
    tmGrammar.TAU: (0, 11),
}
"""Limits for slice cuts on object collections."""

# -----------------------------------------------------------------------------
#  Regular expressions
# -----------------------------------------------------------------------------

RegExFloatingPoint = re.compile(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)")
"""Regular expression to match floating points."""

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def getScale(scales, name: str) -> List:
    try:
        return scales.bins[name]
    except IndexError:
        return []


def createVerticalSpacerItem(width: int = 0, height: int = 0):
    """Returns a new vertical QSpacerItem instance."""
    horizontalPolicy = QtWidgets.QSizePolicy.MinimumExpanding
    verticalPolicy = QtWidgets.QSizePolicy.MinimumExpanding
    return QtWidgets.QSpacerItem(width, height, horizontalPolicy, verticalPolicy)


def calculateRange(specification, scales) -> RangeType:
    """Returns calcualted range for linear cut."""
    # Unconstrained pt
    if specification.type == tmGrammar.UPT:
        def isMuUpt(scale): # filter
            return scale[kObject] == tmGrammar.MU and scale[kType] == tmGrammar.UPT
        for scale in filter(isMuUpt, scales.scales):
            minimum = float(scale[kMinimum])
            maximum = float(scale[kMaximum])
            return minimum, maximum
        return 0.0, 0.0
    # Delta eta
    if specification.type in (tmGrammar.DETA, tmGrammar.ORMDETA):
        def isMuEta(scale): # filter
            return scale[kObject] == tmGrammar.MU and scale[kType] == tmGrammar.ETA
        def isJetEta(scale): # filter
            return scale[kObject] == tmGrammar.JET and scale[kType] == tmGrammar.ETA
        for scaleMu in filter(isMuEta, scales.scales):
            for scaleCalo in filter(isJetEta, scales.scales):
                scale = scaleMu if scaleMu[kMaximum] > scaleCalo[kMaximum] else scaleCalo
                minimum = 0.0
                maximum = float(scale[kMaximum]) * 2.0
                return minimum, maximum
            return 0.0, 0.0
    # Delta phi
    if specification.type in (tmGrammar.DPHI, tmGrammar.ORMDPHI):
        minimum = 0.0
        maximum = math.pi
        return minimum, maximum
    # Delta-R
    if specification.type in (tmGrammar.DR, tmGrammar.ORMDR):
        return calculateDRRange()
    # Invariant mass
    if specification.type == tmGrammar.MASS:
        return calculateInvMassRange()
    # Invariant mass for unconstained pt
    if specification.type == tmGrammar.MASSUPT:
        return calculateInvMassRange()
    # Invariant mass/delta-R
    if specification.type == tmGrammar.MASSDR:
        return 0.0, 1e8
    # Two body pt
    if specification.type == tmGrammar.TBPT:
        return calculateTwoBodyPtRange()
    # Slices
    if specification.type == tmGrammar.SLICE:
        return ObjectCollectionRanges[specification.object]
    # Anomaly score
    if specification.type == tmGrammar.ASCORE:
        return 0.0, 1e8
    # NN score (different models, max. 32 bits)
    if specification.type == tmGrammar.SCORE:
        return 0.0, 2**32
    # CICADA score
    if specification.type == tmGrammar.CSCORE:
        def isCScore(scale):
            return scale[kObject] == tmGrammar.CICADA and scale[kType] == tmGrammar.CSCORE
        for scale in filter(isCScore, scales.scales):
            minimum = float(scale[kMinimum])
            maximum = float(scale[kMaximum])
            return minimum, maximum
        return 0.0, 2**8  # TODO fallback
    raise RuntimeError(f"Invalid cut type: {specification.type}")

def calculateStep(specification, scales) -> float:
    """Calculate dynamic or static range step for cut (experimental)."""
    # CICADA score
    if specification.type == tmGrammar.CSCORE:
        def isPrecisionCScore(scale):
            return scale[kObject] == "PRECISION" and scale[kType] == f"{tmGrammar.CICADA}-{tmGrammar.CSCORE}"
        for scale in filter(isPrecisionCScore, scales.scales):
            n_bits = float(scale[kNBits])
            return 1 / (2**n_bits)
        return specification.range_step
    return specification.range_step

# -----------------------------------------------------------------------------
#  Exception classes
# -----------------------------------------------------------------------------

class CutEditorError(Exception):
    pass

# -----------------------------------------------------------------------------
#  Scale spin box widgets
# -----------------------------------------------------------------------------

class ScaleSpinBox(QtWidgets.QDoubleSpinBox):
    """Custom spin box for scales lookup table."""

    MinimumMode = kMinimum
    MaximumMode = kMaximum
    EmptyScale = [{kNumber: 0, kMinimum: .0, kMaximum: .0}]

    def __init__(self, mode=MinimumMode, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setMode(mode)
        self.setScale(self.EmptyScale)

    def reset(self):
        self.setScale(self.EmptyScale)

    def setMode(self, mode):
        self.mode = mode

    def setScale(self, scale, prec=3):
        """Scale requires a list of dictionaries with at least a *number*,
        *minimum* and *maximum* keys. *mode* specifies if the upper or lower bin
         limit is used."""
        # Important: sort the scale set by minimum or maximum - not by numbers (encoded in two's complement).
        self.scale = sorted(scale, key=lambda bin: float(bin[self.mode]))
        self.index = 0
        self.setDecimals(prec)
        minimum = min([float(value[self.mode]) for value in self.scale] or [0.])
        maximum = max([float(value[self.mode]) for value in self.scale] or [0.])
        self.setRange(minimum, maximum)

    def stepBy(self, steps):
        self.index += steps
        self.setValue(float(self.scale[self.index][self.mode]))

    def value(self, index=None):
        """Returns floating point value by bin index (upper or lower depending on mode)."""
        if index == None:
            index = self.index
        return float(self.scale[index][self.mode])

    def minimum(self):
        return self.value(0)

    def maximum(self):
        return self.value(-1)

    def setValue(self, value):
        value = self.nearest(value)
        super().setValue(value)

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        results = RegExFloatingPoint.findall(text)
        if results:
            return self.nearest(float(results[0]))
        return None

    def nearest(self, value):
        """Returns nearest neighbor of value in range."""
        # See also "finding index of an item closest to the value in a list that's not entirely sorted"
        # http://stackoverflow.com/questions/9706041/finding-index-of-an-item-closest-to-the-value-in-a-list-thats-not-entirely-sort
        result = min(range(len(self.scale)), key=lambda i: abs(float(self.scale[i][self.mode]) - float(value)))
        self.index = result
        return self.value(self.index)

# -----------------------------------------------------------------------------
#  Range spin box class
# -----------------------------------------------------------------------------

class RangeSpinBox(QtWidgets.QDoubleSpinBox):
    """Custom spin box for fixed stepped ranges."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

    def setMinimum(self, minimum):
        super().setMinimum(self.nearest(minimum))

    def setMaximum(self, maximum):
        super().setMaximum(self.nearest(maximum))

    def setRange(self, minimum, maximum):
        super().setRange(self.nearest(minimum), self.nearest(maximum))

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        value, ok = QtCore.QLocale.system().toDouble(self.cleanText())
        return self.nearest(value)

    def nearest(self, value):
        """Returns nearest neighbor of value in range."""
        step = self.singleStep()
        return round(value / step) * step


# -----------------------------------------------------------------------------
#  Inout widget classes
# -----------------------------------------------------------------------------

class InputWidget(QtWidgets.QWidget):
    """Abstract input widget.

    >>> widget.loadCut(cut)
    >>> widget.updateCut(cut)
    """

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.specification = specification
        self.scales = scales

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        raise NotImplementedError()

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        raise NotImplementedError()


class ScaleWidget(InputWidget):
    """Provides scales range entries."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()
        self.initRange()

    def setupUi(self):
        # Create labels
        self.minimumLabel = QtWidgets.QLabel(self.tr("Minimum"), self)
        self.minimumLabel.setObjectName("minimumLabel")
        self.maximumLabel = QtWidgets.QLabel(self.tr("Maximum"), self)
        self.maximumLabel.setObjectName("maximumLabel")
        # Create minimum input widget
        self.minimumSpinBox = ScaleSpinBox(ScaleSpinBox.MinimumMode, self)
        self.minimumSpinBox.setObjectName("minimumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.minimumSpinBox.sizePolicy().hasHeightForWidth())
        self.minimumSpinBox.setSizePolicy(sizePolicy)
        if self.specification.range_unit:
            self.minimumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create maximum input widget
        self.maximumSpinBox = ScaleSpinBox(ScaleSpinBox.MaximumMode, self)
        self.maximumSpinBox.setObjectName("maximumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.maximumSpinBox.sizePolicy().hasHeightForWidth())
        self.maximumSpinBox.setSizePolicy(sizePolicy)
        if self.specification.range_unit:
            self.maximumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Optional eta/phi graphs
        self.etaCutChart = EtaCutChart(self)
        self.etaCutChart.hide()
        self.phiCutChart = PhiCutChart(self)
        self.phiCutChart.hide()
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.minimumLabel, 0, 0)
        layout.addWidget(self.minimumSpinBox, 0, 1)
        layout.addWidget(self.maximumLabel, 1, 0)
        layout.addWidget(self.maximumSpinBox, 1, 1)
        layout.addWidget(self.etaCutChart, 2, 1, 1, 2)
        layout.addWidget(self.phiCutChart, 3, 1, 1, 2)
        layout.addItem(createVerticalSpacerItem())
        self.setLayout(layout)
        self.minimumSpinBox.valueChanged.connect(self.updateCharts)
        self.maximumSpinBox.valueChanged.connect(self.updateCharts)

    def initRange(self):
        scale = getScale(self.scales, self.specification.name)
        self.minimumSpinBox.setScale(scale, self.specification.range_precision)
        self.maximumSpinBox.setScale(scale, self.specification.range_precision)
        minimum = self.minimumSpinBox.minimum()
        maximum = self.maximumSpinBox.maximum()
        self.minimumSpinBox.setValue(minimum)
        self.maximumSpinBox.setValue(maximum)

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        self.minimumSpinBox.setValue(float(cut.minimum))
        self.maximumSpinBox.setValue(float(cut.maximum))

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        cut.minimum = self.minimumSpinBox.value()
        cut.maximum = self.maximumSpinBox.value()
        cut.data = ""

    def updateCharts(self):
        """Update optional charts for eta and phi."""
        if self.specification.type == tmGrammar.ETA:
            self.etaCutChart.setRange(self.minimumSpinBox.value(), self.maximumSpinBox.value())
            self.etaCutChart.update()
            self.etaCutChart.show()
        elif self.specification.type == tmGrammar.PHI:
            self.phiCutChart.setRange(self.minimumSpinBox.value(), self.maximumSpinBox.value())
            self.phiCutChart.update()
            self.phiCutChart.show()


class RangeWidget(InputWidget):
    """Provides range entries."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()
        self.initRange()

    def setupUi(self):
        # Create labels
        self.minimumLabel = QtWidgets.QLabel(self.tr("Minimum"), self)
        self.minimumLabel.setObjectName("minimumLabel")
        self.maximumLabel = QtWidgets.QLabel(self.tr("Maximum"), self)
        self.maximumLabel.setObjectName("maximumLabel")
        # Create minimum input widget
        self.minimumSpinBox = RangeSpinBox(self)
        self.minimumSpinBox.setObjectName("minimumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.minimumSpinBox.sizePolicy().hasHeightForWidth())
        self.minimumSpinBox.setSizePolicy(sizePolicy)
        self.minimumSpinBox.setSingleStep(self.specification.range_step)
        self.minimumSpinBox.setDecimals(self.specification.range_precision)
        if self.specification.range_unit:
            self.minimumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create maximum input widget
        self.maximumSpinBox = RangeSpinBox(self)
        self.maximumSpinBox.setObjectName("maximumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.maximumSpinBox.sizePolicy().hasHeightForWidth())
        self.maximumSpinBox.setSizePolicy(sizePolicy)
        self.maximumSpinBox.setSingleStep(self.specification.range_step)
        self.maximumSpinBox.setDecimals(self.specification.range_precision)
        if self.specification.range_unit:
            self.maximumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.minimumLabel, 0, 0)
        layout.addWidget(self.minimumSpinBox, 0, 1)
        layout.addWidget(self.maximumLabel, 1, 0)
        layout.addWidget(self.maximumSpinBox, 1, 1)
        layout.addItem(createVerticalSpacerItem())
        self.setLayout(layout)

    def initRange(self):
        """Set range for inputs."""
        minimum, maximum = calculateRange(self.specification, self.scales)
        self.minimumSpinBox.setRange(minimum, maximum)
        self.maximumSpinBox.setRange(minimum, maximum)
        minimum = self.minimumSpinBox.minimum()
        maximum = self.maximumSpinBox.maximum()
        self.minimumSpinBox.setValue(minimum)
        self.maximumSpinBox.setValue(maximum)

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        self.minimumSpinBox.setValue(float(cut.minimum))
        self.maximumSpinBox.setValue(float(cut.maximum))

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        cut.minimum = self.minimumSpinBox.value()
        cut.maximum = self.maximumSpinBox.value()
        cut.data = ""

class InfiniteRangeWidget(InputWidget):
    """Provides range entries with infinity option."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()
        self.initRange()

    def setupUi(self):
        # Create labels
        self.minimumLabel = QtWidgets.QLabel(self.tr("Minimum"), self)
        self.minimumLabel.setObjectName("minimumLabel")
        self.maximumLabel = QtWidgets.QLabel(self.tr("Maximum"), self)
        self.maximumLabel.setObjectName("maximumLabel")
        # Create minimum input widget
        self.minimumSpinBox = RangeSpinBox(self)
        self.minimumSpinBox.setObjectName("minimumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.minimumSpinBox.sizePolicy().hasHeightForWidth())
        self.minimumSpinBox.setSizePolicy(sizePolicy)
        self.minimumSpinBox.setSingleStep(self.specification.range_step)
        self.minimumSpinBox.setDecimals(self.specification.range_precision)
        self.minimumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create maximum input widget
        self.maximumSpinBox = RangeSpinBox(self)
        self.maximumSpinBox.setObjectName("maximumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.maximumSpinBox.sizePolicy().hasHeightForWidth())
        self.maximumSpinBox.setSizePolicy(sizePolicy)
        self.maximumSpinBox.setSingleStep(self.specification.range_step)
        self.maximumSpinBox.setDecimals(self.specification.range_precision)
        self.maximumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create infinite check box
        self.infiniteCheckBox = QtWidgets.QCheckBox(self.tr("&Infinite open"), self)
        self.infiniteCheckBox.setObjectName("infiniteCheckBox")
        self.infiniteCheckBox.setChecked(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.infiniteCheckBox.sizePolicy().hasHeightForWidth())
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.minimumLabel, 0, 0)
        layout.addWidget(self.minimumSpinBox, 0, 1)
        layout.addWidget(self.maximumLabel, 1, 0)
        layout.addWidget(self.maximumSpinBox, 1, 1)
        layout.addWidget(self.infiniteCheckBox, 2, 1)
        layout.addItem(createVerticalSpacerItem())
        self.setLayout(layout)
        # Connections
        self.infiniteCheckBox.stateChanged.connect(self.updateInfinitiyOption)
        self.updateInfinitiyOption()

    def initRange(self):
        """Set range for inputs."""
        minimum, maximum = calculateRange(self.specification, self.scales)
        self.minimumSpinBox.setRange(minimum, maximum)
        self.maximumSpinBox.setRange(minimum, maximum)
        minimum = self.minimumSpinBox.minimum()
        maximum = self.maximumSpinBox.maximum()
        self.minimumSpinBox.setValue(minimum)
        self.maximumSpinBox.setValue(maximum)

    def updateInfinitiyOption(self):
        """Slot called if infinity check box is checked."""
        checked = self.infiniteCheckBox.isChecked()
        self.maximumSpinBox.setEnabled(not checked)
        if checked:
            maximum = self.maximumSpinBox.maximum()
            self.maximumSpinBox.setValue(maximum)

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        self.minimumSpinBox.setValue(float(cut.minimum))
        self.maximumSpinBox.setValue(float(cut.maximum))
        infinite = self.maximumSpinBox.value() >= self.maximumSpinBox.maximum()
        self.infiniteCheckBox.setChecked(infinite)

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        minimum = self.minimumSpinBox.value()
        maximum = self.maximumSpinBox.value()
        if maximum <= minimum:
            raise CutEditorError("Invalid range: [{0}-{1}] (minimum<maximum)!".format(minimum, maximum))
        cut.minimum = minimum
        cut.maximum = maximum
        cut.data = ""


class SliceWidget(InputWidget):
    """Provides slice selection entries, using cut minimum/maximum."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()
        self.initRange()

    def setupUi(self):
        # Create widgets
        self.beginLabel = QtWidgets.QLabel(self.tr("Begin"), self)
        self.beginLabel.setObjectName("beginLabel")
        self.endLabel = QtWidgets.QLabel(self.tr("End"), self)
        self.endLabel.setObjectName("endLabel")
        self.beginSpinBox = QtWidgets.QSpinBox(self)
        self.beginSpinBox.setObjectName("beginSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.beginSpinBox.sizePolicy().hasHeightForWidth())
        self.beginSpinBox.setSizePolicy(sizePolicy)
        self.endSpinBox = QtWidgets.QSpinBox(self)
        self.endSpinBox.setObjectName("endSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.endSpinBox.sizePolicy().hasHeightForWidth())
        self.endSpinBox.setSizePolicy(sizePolicy)
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.beginLabel, 0, 0)
        layout.addWidget(self.beginSpinBox, 0, 1)
        layout.addWidget(self.endLabel, 1, 0)
        layout.addWidget(self.endSpinBox, 1, 1)
        layout.addItem(createVerticalSpacerItem())
        self.setLayout(layout)

    def initRange(self):
        """Set range for inputs."""
        minimum, maximum = calculateRange(self.specification, self.scales)
        self.beginSpinBox.setRange(minimum, maximum)
        self.endSpinBox.setRange(minimum, maximum)
        minimum = self.beginSpinBox.minimum()
        maximum = self.endSpinBox.maximum()
        self.beginSpinBox.setValue(minimum)
        self.endSpinBox.setValue(maximum)

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        self.beginSpinBox.setValue(int(cut.minimum))
        self.endSpinBox.setValue(int(cut.maximum))

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        begin = self.beginSpinBox.value()
        end = self.endSpinBox.value()
        if begin > end:
            raise CutEditorError("Invalid slice range: [{0}-{1}] (begin<end)!".format(begin, end))
        cut.minimum = begin
        cut.maximum = end
        cut.data = ""


class ThresholdWidget(InputWidget):
    """Provides a single threshold entry, using only cut minimum."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()
        self.initRange()

    def setupUi(self):
        # Create labels
        self.thresholdLabel = QtWidgets.QLabel(self.tr("Threshold"), self)
        self.thresholdLabel.setObjectName("thresholdLabel")
        # Create threshold input widget
        self.thresholdSpinBox = RangeSpinBox(self)
        self.thresholdSpinBox.setObjectName("thresholdSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.thresholdSpinBox.sizePolicy().hasHeightForWidth())
        self.thresholdSpinBox.setSizePolicy(sizePolicy)
        self.thresholdSpinBox.setSingleStep(self.specification.range_step)
        self.thresholdSpinBox.setDecimals(self.specification.range_precision)
        self.thresholdSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.thresholdLabel, 0, 0)
        layout.addWidget(self.thresholdSpinBox, 0, 1)
        layout.addItem(createVerticalSpacerItem())
        self.setLayout(layout)

    def initRange(self):
        """Set range for inputs."""
        minimum, maximum = calculateRange(self.specification, self.scales)
        self.thresholdSpinBox.setRange(minimum, maximum)
        step = calculateStep(self.specification, self.scales)
        self.thresholdSpinBox.setSingleStep(step)
        minimum = self.thresholdSpinBox.minimum()
        self.thresholdSpinBox.setValue(minimum)

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        self.thresholdSpinBox.setValue(float(cut.minimum))

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        cut.minimum = self.thresholdSpinBox.value()
        cut.maximum = 0.
        cut.data = ""


class KeyWidget(InputWidget):
    """Provides a line edit entry for keys (eg. TOPO models)."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()

    def setupUi(self):
        # Create labels
        self.keyLabel = QtWidgets.QLabel(self.tr("Key"), self)
        self.keyLabel.setObjectName("keyLabel")
        # Create threshold input widget
        self.keyLineEdit = QtWidgets.QLineEdit()
        self.keyLineEdit.setObjectName("keyLineEdit")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.keyLineEdit.sizePolicy().hasHeightForWidth())
        self.keyLineEdit.setSizePolicy(sizePolicy)
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.keyLabel, 0, 0)
        layout.addWidget(self.keyLineEdit, 0, 1)
        layout.addItem(createVerticalSpacerItem())
        self.setLayout(layout)
        validator = QtGui.QRegExpValidator(QtCore.QRegExp("[a-z0-9_]*"))
        self.keyLineEdit.setValidator(validator)

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        self.keyLineEdit.setText(cut.data)

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        cut.data = self.keyLineEdit.text()


class MaximumWidget(InputWidget):
    """Provides a maximum only entriy."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()
        self.initRange()

    def setupUi(self):
        # Create labels
        self.maximumLabel = QtWidgets.QLabel(self.tr("Maximum"), self)
        self.maximumLabel.setObjectName("maximumLabel")
        # Create maximum input widget
        self.maximumSpinBox = RangeSpinBox(self)
        self.maximumSpinBox.setObjectName("maximumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.maximumSpinBox.sizePolicy().hasHeightForWidth())
        self.maximumSpinBox.setSizePolicy(sizePolicy)
        self.maximumSpinBox.setSingleStep(self.specification.range_step)
        self.maximumSpinBox.setDecimals(self.specification.range_precision)
        self.maximumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.maximumLabel, 0, 0)
        layout.addWidget(self.maximumSpinBox, 0, 1)
        layout.addItem(createVerticalSpacerItem())
        self.setLayout(layout)

    def initRange(self):
        """Set range for inputs."""
        minimum, maximum = calculateRange(self.specification, self.scales)
        self.maximumSpinBox.setRange(minimum, maximum)
        minimum = self.maximumSpinBox.minimum()
        self.maximumSpinBox.setValue(minimum)

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        self.maximumSpinBox.setValue(float(cut.maximum))

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        cut.minimum = 0.
        cut.maximum = self.maximumSpinBox.value()
        cut.data = ""


class MultipleJoiceWidget(InputWidget):
    """Provides a multiple joice entry."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()

    def setupUi(self):
        # Create widgets
        self.scrollAreaLabel = QtWidgets.QLabel(self.tr("Data"), self)
        self.scrollAreaLabel.setObjectName("scrollAreaLabel")
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidgetResizable(True)
        content = self.createScrollAreaContent()
        self.scrollArea.setWidget(content)
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scrollAreaLabel)
        layout.addWidget(self.scrollArea)
        self.setLayout(layout)

    def format_label(self, key, value):
        """Check box label formatter provided for overlaoding."""
        return value

    def createScrollAreaContent(self):
        widget = QtWidgets.QWidget(self)
        widget.setObjectName("widget")
        vbox = QtWidgets.QVBoxLayout()
        self.options = {}
        for key, value in self.sortedItems():
            option = QtWidgets.QCheckBox(self.format_label(key, value), self)
            option.data = key
            vbox.addWidget(option)
            self.options[key] = option
        vbox.addItem(createVerticalSpacerItem())
        widget.setLayout(vbox)
        return widget

    def sortedItems(self):
        """Returns data items, sorted by keys."""
        items = self.specification.data.items()
        return sorted(items, key=lambda items: toolbox.natural_sort_key(items[0]))

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        tokens = [token.strip() for token in cut.data.split(",")]
        for token in tokens:
            if token not in self.options.keys():
                raise CutEditorError("Invalid cut data: {0}".format(token))
            self.options[token].setChecked(True)

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        tokens = []
        for key, value in self.sortedItems(): # order!
            if self.options[key].isChecked():
                tokens.append(key)
        if not tokens:
            raise CutEditorError("No option checked!")
        cut.minimum = 0.0
        cut.maximum = 0.0
        cut.data = ",".join(tokens)


class MultipleJoiceIsoWidget(MultipleJoiceWidget):
    """Provides a multiple joice entry for isolation."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)

    def format_label(self, key, value):
        """Check box label formatter provided for overlaoding."""
        index = int(key)
        return f"[0b{index:02b}] {value}"


class SingleJoiceWidget(InputWidget):
    """Provides a single joice entry."""

    def __init__(self, specification, scales, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(specification, scales, parent)
        self.setupUi()

    def setupUi(self):
        # Create widgets
        self.scrollAreaLabel = QtWidgets.QLabel(self.tr("Data"), self)
        self.scrollAreaLabel.setObjectName("scrollAreaLabel")
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidgetResizable(True)
        content = self.createScrollAreaContent()
        self.scrollArea.setWidget(content)
        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scrollAreaLabel)
        layout.addWidget(self.scrollArea)
        self.setLayout(layout)

    def createScrollAreaContent(self):
        widget = QtWidgets.QWidget(self)
        widget.setObjectName("widget")
        vbox = QtWidgets.QVBoxLayout()
        self.options = {}
        for key, value in self.sortedItems():
            option = QtWidgets.QRadioButton(value, self)
            option.data = key
            vbox.addWidget(option)
            self.options[key] = option
        vbox.addItem(createVerticalSpacerItem())
        widget.setLayout(vbox)
        return widget

    def sortedItems(self):
        """Returns data items, sorted by keys."""
        items = self.specification.data.items()
        return sorted(items, key=lambda items: toolbox.natural_sort_key(items[0]))

    def loadCut(self, cut):
        """Initialize widget from cut item."""
        token = cut.data.strip()
        if token not in self.options.keys():
            raise CutEditorError("Invalid cut data: {0}".format(token))
        self.options[token].setChecked(True)

    def updateCut(self, cut):
        """Update existing cut from inputs."""
        token = None
        for key, button in self.options.items():
            if button.isChecked():
                token = key
                break
        if not token:
            raise CutEditorError("No option checked!")
        cut.minimum = 0.0
        cut.maximum = 0.0
        cut.data = token

# -----------------------------------------------------------------------------
#  Inout widget classes
# -----------------------------------------------------------------------------

class CutTreeWidget(QtWidgets.QTreeWidget):
    """Tree widget displaying cut types hierarchical."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

    def loadCutSpecs(self, specs):
        """Initialize tree widget using a list of cut specifications."""
        # TODO
        self.clear()
        for spec in specs:
            pass

    def addRootItem(self, name, widget):
        """Add new root item for tree widget."""
        # TODO
        item = QtWidgets.QTreeWidgetItem(self)
        item.setText(0, name)
        item.spec = None
        item.widget = widget
        return item

    def addCutItem(self, parent, spec, widget):
        """Add new cut item for tree widget."""
        # TODO
        item = QtWidgets.QTreeWidgetItem(parent)
        item.spec = spec # Attach cut spec to item data
        item.setText(0, spec.type)
        item.widget = widget
        return item


class CutEditorDialog(QtWidgets.QDialog):
    """Cut editor dialog."""

    InputWidgetFactory = {
        # Object cuts
        tmGrammar.UPT: InfiniteRangeWidget,
        tmGrammar.ETA: ScaleWidget,
        tmGrammar.PHI: ScaleWidget,
        tmGrammar.ISO: MultipleJoiceIsoWidget,
        tmGrammar.QLTY: MultipleJoiceWidget,
        tmGrammar.DISP: SingleJoiceWidget,
        tmGrammar.CHG: SingleJoiceWidget,
        tmGrammar.IP: MultipleJoiceWidget,
        tmGrammar.SLICE: SliceWidget,
        tmGrammar.INDEX: ScaleWidget,
        tmGrammar.ASCORE: ThresholdWidget,
        tmGrammar.SCORE: ThresholdWidget,
        tmGrammar.MODEL: KeyWidget,
        tmGrammar.CSCORE: ThresholdWidget,
        # Function cuts
        tmGrammar.CHGCOR: SingleJoiceWidget,
        tmGrammar.DETA: RangeWidget,
        tmGrammar.DPHI: RangeWidget,
        tmGrammar.DR: InfiniteRangeWidget,
        tmGrammar.MASS: InfiniteRangeWidget,
        tmGrammar.MASSUPT: InfiniteRangeWidget,
        tmGrammar.MASSDR: ThresholdWidget,
        tmGrammar.TBPT: ThresholdWidget,
        tmGrammar.ORMDETA: MaximumWidget,
        tmGrammar.ORMDPHI: MaximumWidget,
        tmGrammar.ORMDR: MaximumWidget,
    }
    """Widget factory for different cut input types."""

    def __init__(self, menu, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """Create new dialog window."""
        super().__init__(parent)
        self.menu = menu
        self.copyMode = False
        self.loadedCut = None
        self.setupUi()

    def setupUi(self):
        """Setup dialog window."""
        # Window
        self.setWindowTitle(self.tr("Cut Editor"))
        self.resize(800, 480)
        # Type selector
        self.treeWidget = CutTreeWidget(self)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.setProperty("showDropIndicator", QtCore.QVariant(False))
        self.treeWidget.header().setVisible(False)
        # Stack widget
        self.stackWidget = QtWidgets.QStackedWidget(self)
        self.stackWidget.setMinimumWidth(250)
        # Suffix
        self.suffixLabel = QtWidgets.QLabel("Suffix", self)
        self.suffixLabel.setObjectName("suffixLabel")
        self.suffixLineEdit = RestrictedLineEdit(self)
        self.suffixLineEdit.setObjectName("suffixLineEdit")
        self.suffixLineEdit.setRegexPattern("[a-zA-Z0-9_]+")
        self.suffixLineEdit.setText(self.tr("Unnamed"))
        # Description
        self.textBrowser = QtWidgets.QTextBrowser(self)
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setMinimumWidth(220)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setReadOnly(True)
        # Comment
        self.commentLabel = QtWidgets.QLabel("Comment", self)
        self.commentLabel.setObjectName("commentLabel")
        self.commentTextEdit = RestrictedPlainTextEdit(self)
        self.commentTextEdit.setObjectName("commentTextEdit")
        # Buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel |
            QtWidgets.QDialogButtonBox.Ok
        )
        # Layout
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.treeWidget, 0, 0, 5, 1)
        layout.addWidget(self.suffixLabel, 0, 1)
        layout.addWidget(self.suffixLineEdit, 1, 1)
        layout.addWidget(self.stackWidget, 2, 1)
        layout.addWidget(self.commentLabel, 3, 1)
        layout.addWidget(self.commentTextEdit, 4, 1)
        layout.addWidget(self.textBrowser, 0, 2, 5, 1)
        layout.addWidget(self.buttonBox, 5, 0, 1, 3)
        self.setLayout(layout)
        # Connections
        self.treeWidget.itemSelectionChanged.connect(self.showSelectedCut)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # Initial calls
        self.showSelectedCut()

    def setupCuts(self, specifictions):
        """Setup dialog by providing a list of cut specifications."""
        # Initialize tree widget
        self.treeWidget.loadCutSpecs(specifictions)
        # Clear stack
        while self.stackWidget.count():
            self.stackWidget.removeWidget(self.stackWidget.currentWidget())
        self.stackWidget.addWidget(QtWidgets.QWidget(self))
        # TODO
        rootItems = {}
        self._items = []
        scales = self.menu.scales
        for spec in specifictions:
            # Check if item is disabled: { enabled: false } [optional]
            if not spec.enabled:
                continue
            # Create root item key
            key = spec.object
            if spec.type in FunctionCutTypes:
                key = "Functions" # Root entry for function cuts
            # If key does not exist, create an empty entry
            if key not in rootItems:
                widget = self.stackWidget.widget(0)
                rootItems[key] = self.treeWidget.addRootItem(key, widget)
            root = rootItems[key]
            # On missing scale (editing outdated XML?)
            if spec.type in (tmGrammar.ETA, tmGrammar.PHI, tmGrammar.UPT, tmGrammar.INDEX):
                if spec.name not in scales.bins:
                    widget = self.stackWidget.widget(0)
                    item = self.treeWidget.addCutItem(root, spec, widget) # TODO
                    item.setDisabled(True)
                    continue
            # Create entry widget
            widget = self.InputWidgetFactory[spec.type](spec, scales, self)
            item = self.treeWidget.addCutItem(root, spec, widget)
            # Add input form to stack
            self.stackWidget.addWidget(item.widget)
            self._items.append(item)

    def loadCut(self, cut):
        """Initialize dialog from existing cut."""
        self.loadedCut = cut
        self.suffixLineEdit.setText(cut.suffix)
        self.suffixLineEdit.setEnabled(not list(filter(lambda algorithm: cut.name in algorithm.cuts(), self.menu.algorithms)))
        if self.copyMode:
            self.suffixLineEdit.setEnabled(True) # HACK overrule on copy
        if cut.isFunctionCut: # TODO not efficient
            result = list(filter(lambda item: item.spec.type == cut.type, self._items))
        else:
            result = list(filter(lambda item: item.spec.object == cut.object and item.spec.type == cut.type, self._items))
        if result:
            logging.debug("result %s", result)
            self.treeWidget.setCurrentItem(result[0])
            item = self.currentTreeItem()
            item.widget.loadCut(cut)
        else:
            raise CutEditorError("Cut type not found: {0}".format(cut.type))
        self.commentTextEdit.setPlainText(cut.comment)
        self.treeWidget.setEnabled(False)

    def updateCut(self, cut):
        """Update existing cut from dialog inputs."""
        item = self.currentTreeItem()
        if not item or not item.spec: # No cut type selected (eg. parent nodes)
            raise CutEditorError(
                self.tr("No cut type selected.")
            )
        item.widget.updateCut(cut)
        cut.object = item.widget.specification.object
        cut.type = item.widget.specification.type
        suffix = self.suffixLineEdit.text()
        cut.name = "{0}_{1}".format(cut.typename, suffix)
        cut.comment = self.commentTextEdit.toPlainText()
        cut.modified = True

    def newCut(self):
        """Create new cut from dialog inputs."""
        cut = Cut("", "", "") # Create empty cut
        self.updateCut(cut)
        return cut

    def validateSuffix(self, cut):
        """Validate suffix, check for empty or duplicated name, raises a ValidationException on error."""
        # Empty suffix?
        if not len(self.suffixLineEdit.text()):
            raise CutEditorError(
                self.tr("No suffix is given. It must be at least one character in length.")
            )
        # Name already used?
        if cut.name in [cut_.name for cut_ in self.menu.cuts]:
            duplicates = list(filter(lambda cut_: cut_.name == cut.name, self.menu.cuts))
            isConflict = (self.loadedCut and self.loadedCut in duplicates)
            if (self.copyMode and isConflict) or (not isConflict): # wired...
                raise CutEditorError(
                    self.tr("Suffix \"{0}\" is already used with a cut of type \"{1}\".").format(cut.suffix, cut.type)
                )

    def validate(self):
        """Validate user entries."""
        cut = self.newCut()
        self.validateSuffix(cut) # TODO

    def currentTreeItem(self):
        """Returns current selected tree item."""
        items = self.treeWidget.selectedItems()
        if items:
            return items[0]
        return None

    def updateDescription(self):
        """Update description text browser."""
        self.textBrowser.setHtml(self.tr("Select a cut type..."))
        item = self.currentTreeItem()
        if item and item.spec:
            description = []
            description = ["<h3>{0} cut</h3>{1}".format(item.spec.title, item.spec.description)]
            if item.spec.functions:
                description.append("<h4>Compatible functions:</h4>")
                description.append("<ul>")
                for function in item.spec.functions:
                    # ignore depricated mass function
                    if function not in [tmGrammar.mass]:
                        description.append("<li><span style=\"color:blue;font-weight:bold;\">{0}</span>{{ ... }}[{1}_N, ...]</li>".format(function, item.spec.type))
                description.append("</ul>")
            if item.spec.objects:
                description.append("<h4>Compatible object types:</h4>")
                description.append("<ul>")
                for obj in item.spec.objects:
                    description.append("<li><span>{0}</span></li>".format(obj))
                description.append("</ul>")
            self.textBrowser.setHtml("".join(description))

    @QtCore.pyqtSlot()
    def showSelectedCut(self):
        """Show input widget for selected cut type."""
        self.updateDescription()
        item = self.currentTreeItem()
        if item:
            self.stackWidget.setCurrentWidget(item.widget)

    @QtCore.pyqtSlot()
    def accept(self):
        """Overloaded slot for accept()."""
        try:
            self.validate()
        except CutEditorError as exc:
            logging.warning(format(exc))
            QtWidgets.QMessageBox.warning(self, "Validation error", format(exc))
        else:
            super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        """Overloaded slot for reject()."""
        super().reject()
