import tmGrammar

from tmEditor.core.types import ObjectCutTypes, FunctionCutTypes
from tmEditor.core.Menu import Menu
from tmEditor.core.Algorithm import Cut
from tmEditor.core import XmlDecoder
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

from tmEditor.PyQt5Proxy import (
    QtCore,
    QtWidgets,
    pyqt4_str,
    pyqt4_toPyObject
)

import math
import logging
import re

__all__ = ["CutEditorDialog"]

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kComment = 'comment'
kData = 'data'
kMaximum = 'maximum'
kMinimum = 'minimum'
kName = 'name'
kNumber = 'number'
kType = 'type'
kObject = 'object'

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

RegExFloatingPoint = re.compile(r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)')
"""Regular expression to match floating points."""

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def createVerticalSpacerItem(width=0, height=0):
    """Returns a new vertical QSpacerItem instance."""
    horizontalPolicy = QtWidgets.QSizePolicy.MinimumExpanding
    verticalPolicy = QtWidgets.QSizePolicy.MinimumExpanding
    return QtWidgets.QSpacerItem(width, height, horizontalPolicy, verticalPolicy)

def calculateRange(specification, scales):
    """Returns calcualted range for linear cut."""
    # Delta eta
    if specification.type in (tmGrammar.DETA, tmGrammar.ORMDETA):
        def isMuEta(scale): # filter
            return scale[kObject]==tmGrammar.MU and scale[kType]==tmGrammar.ETA
        def isJetEta(scale): # filter
            return scale[kObject]==tmGrammar.JET and scale[kType]==tmGrammar.ETA
        scaleMu = list(filter(isMuEta, scales.scales))[0]
        scaleCalo = list(filter(isJetEta, scales.scales))[0]
        scale = scaleMu if scaleMu[kMaximum] > scaleCalo[kMaximum] else scaleCalo
        minimum = 0.
        maximum = float(scale[kMaximum]) * 2.
        return minimum, maximum
    # Delta phi
    if specification.type in (tmGrammar.DPHI, tmGrammar.ORMDPHI):
        minimum = 0.
        maximum = math.pi
        return minimum, maximum
    # Delta-R
    if specification.type in (tmGrammar.DR, tmGrammar.ORMDR):
        return calculateDRRange()
    # Invariant mass
    if specification.type == tmGrammar.MASS:
        return calculateInvMassRange()
    # Two body pt
    if specification.type == tmGrammar.TBPT:
        return calculateTwoBodyPtRange()
    # Slices
    if specification.type == tmGrammar.SLICE:
        return ObjectCollectionRanges[specification.object]
    raise RuntimeError("invalid cut type")

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

    def __init__(self, mode=MinimumMode, parent=None):
        super(ScaleSpinBox, self).__init__(parent)
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
        self.scale = sorted(scale, key = lambda bin: float(bin[self.mode]))
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
        if index == None: index = self.index
        return float(self.scale[index][self.mode])

    def minimum(self):
        return self.value(0)

    def maximum(self):
        return self.value(-1)

    def setValue(self, value):
        value = self.nearest(value)
        super(ScaleSpinBox, self).setValue(value)

    def valueFromText(self, text):
        """Re-implementation of valueFromText(), it returns only the nearest."""
        results = RegExFloatingPoint.findall(pyqt4_str(text))
        if results:
            return self.nearest(float(results[0]))

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

    def __init__(self, parent=None):
        super(RangeSpinBox, self).__init__(parent)

    def setMinimum(self, minimum):
        super(RangeSpinBox, self).setMinimum(self.nearest(minimum))

    def setMaximum(self, maximum):
        super(RangeSpinBox, self).setMaxnimum(self.nearest(maximum))

    def setRange(self, minimum, maximum):
        super(RangeSpinBox, self).setRange(self.nearest(minimum), self.nearest(maximum))

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

    def __init__(self, specification, scales, parent=None):
        super(InputWidget, self).__init__(parent)
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

    def __init__(self, specification, scales, parent=None):
        super(ScaleWidget, self).__init__(specification, scales, parent)
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(self.minimumSpinBox.sizePolicy().hasHeightForWidth())
        self.minimumSpinBox.setSizePolicy(sizePolicy)
        if self.specification.range_unit:
            self.minimumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create maximum input widget
        self.maximumSpinBox = ScaleSpinBox(ScaleSpinBox.MaximumMode, self)
        self.maximumSpinBox.setObjectName("maximumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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
        scale = self.scales.bins[self.specification.name]
        self.minimumSpinBox.setScale(scale)
        self.maximumSpinBox.setScale(scale)
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

    def __init__(self, specification, scales, parent=None):
        super(RangeWidget, self).__init__(specification, scales, parent)
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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

    def __init__(self, specification, scales, parent=None):
        super(InfiniteRangeWidget, self).__init__(specification, scales, parent)
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(self.minimumSpinBox.sizePolicy().hasHeightForWidth())
        self.minimumSpinBox.setSizePolicy(sizePolicy)
        self.minimumSpinBox.setSingleStep(self.specification.range_step)
        self.minimumSpinBox.setDecimals(self.specification.range_precision)
        self.minimumSpinBox.setSuffix(" {0}".format(self.specification.range_unit))
        # Create maximum input widget
        self.maximumSpinBox = RangeSpinBox(self)
        self.maximumSpinBox.setObjectName("maximumSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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
        cut.minimum = self.minimumSpinBox.value()
        cut.maximum = self.maximumSpinBox.value()
        cut.data = ""

class SliceWidget(InputWidget):
    """Provides slice selection entries, using cut minimum/maximum."""

    def __init__(self, specification, scales, parent=None):
        super(SliceWidget, self).__init__(specification, scales, parent)
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(self.beginSpinBox.sizePolicy().hasHeightForWidth())
        self.beginSpinBox.setSizePolicy(sizePolicy)
        self.endSpinBox = QtWidgets.QSpinBox(self)
        self.endSpinBox.setObjectName("endSpinBox")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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

    def __init__(self, specification, scales, parent=None):
        super(ThresholdWidget, self).__init__(specification, scales, parent)
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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

class MaximumWidget(InputWidget):
    """Provides a maximum only entriy."""

    def __init__(self, specification, scales, parent=None):
        super(MaximumWidget, self).__init__(specification, scales, parent)
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
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
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

    def __init__(self, specification, scales, parent=None):
        super(MultipleJoiceWidget, self).__init__(specification, scales, parent)
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
        items = self.specification.data.iteritems()
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
        cut.minimum = ""
        cut.maximum = ""
        cut.data = ",".join(tokens)

class MultipleJoiceIsoWidget(MultipleJoiceWidget):
    """Provides a multiple joice entry for isolation."""

    def __init__(self, specification, scales, parent=None):
        super(MultipleJoiceIsoWidget, self).__init__(specification, scales, parent)

    def format_label(self, key, value):
        """Check box label formatter provided for overlaoding."""
        index = int(key)
        return "[0b{index:02b}] {value}".format(**locals())

class SingleJoiceWidget(InputWidget):
    """Provides a single joice entry."""

    def __init__(self, specification, scales, parent=None):
        super(SingleJoiceWidget, self).__init__(specification, scales, parent)
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
        items = self.specification.data.iteritems()
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
        for key, button in self.options.iteritems():
            if button.isChecked():
                token = key
                break
        if not token:
            raise CutEditorError("No option checked!")
        cut.minimum = ""
        cut.maximum = ""
        cut.data = token

# -----------------------------------------------------------------------------
#  Inout widget classes
# -----------------------------------------------------------------------------

class CutTreeWidget(QtWidgets.QTreeWidget):
    """Tree widget displaying cut types hierarchical."""

    def __init__(self, parent=None):
        super(CutTreeWidget, self).__init__(parent)

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
        tmGrammar.ETA: ScaleWidget,
        tmGrammar.PHI: ScaleWidget,
        tmGrammar.ISO: MultipleJoiceIsoWidget,
        tmGrammar.QLTY: MultipleJoiceWidget,
        tmGrammar.CHG: SingleJoiceWidget,
        tmGrammar.SLICE: SliceWidget,
        tmGrammar.CHGCOR: SingleJoiceWidget,
        tmGrammar.DETA: RangeWidget,
        tmGrammar.DPHI: RangeWidget,
        tmGrammar.DR: InfiniteRangeWidget,
        tmGrammar.MASS: InfiniteRangeWidget,
        tmGrammar.TBPT: ThresholdWidget,
        tmGrammar.ORMDETA: MaximumWidget,
        tmGrammar.ORMDPHI: MaximumWidget,
        tmGrammar.ORMDR: MaximumWidget,
    }
    """Widget factory for different cut input types."""

    def __init__(self, menu, parent=None):
        """Create new dialog window."""
        super(CutEditorDialog, self).__init__(parent)
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
        self.treeWidget.setProperty('showDropIndicator', QtCore.QVariant(False))
        self.treeWidget.header().setVisible(False)
        # Stack widget
        self.stackWidget = QtWidgets.QStackedWidget(self)
        self.stackWidget.setMinimumWidth(250)
        # Suffix
        self.suffixLabel = QtWidgets.QLabel("Suffix", self)
        self.suffixLabel.setObjectName("suffixLabel")
        self.suffixLineEdit = RestrictedLineEdit(self)
        self.suffixLineEdit.setObjectName("suffixLineEdit")
        self.suffixLineEdit.setRegexPattern('[a-zA-Z0-9_]+')
        self.suffixLineEdit.setText(self.tr("Unnamed"))
        # Description
        self.textBrowser = QtWidgets.QTextBrowser(self)
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setMinimumWidth(220)
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
            if spec.type in (tmGrammar.ETA, tmGrammar.PHI):
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
            result = filter(lambda item: item.spec.type==cut.type, self._items)
        else:
            result = filter(lambda item: item.spec.object==cut.object and item.spec.type==cut.type, self._items)
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
        if not item: # No cut type selected (eg. parent nodes)
            raise CutEditorError(
                pyqt4_str(self.tr("No cut type selected."))
            )
        item.widget.updateCut(cut)
        cut.object = item.widget.specification.object
        cut.type = item.widget.specification.type
        suffix = pyqt4_str(self.suffixLineEdit.text())
        cut.name = "{0}_{1}".format(cut.typename, suffix)
        cut.comment = pyqt4_str(self.commentTextEdit.toPlainText())
        cut.modified = True

    def newCut(self):
        """Create new cut from dialog inputs."""
        cut = Cut("", "", "") # Create empty cut
        self.updateCut(cut)
        return cut

    def validateSuffix(self, cut):
        """Validate suffix, check for empty or duplicated name, raises a ValidationException on error."""
        # Empty suffix?
        if not len(pyqt4_str(self.suffixLineEdit.text())):
            raise CutEditorError(
                pyqt4_str(self.tr("No suffix is given. It must be at least one character in length."))
            )
        # Name already used?
        if cut.name in [cut_.name for cut_ in self.menu.cuts]:
            duplicates = list(filter(lambda cut_: cut_.name == cut.name, self.menu.cuts))
            isConflict = (self.loadedCut and self.loadedCut in duplicates)
            if (self.copyMode and isConflict) or (not isConflict): # wired...
                raise CutEditorError(
                    pyqt4_str(self.tr("Suffix \"{0}\" is already used with a cut of type \"{1}\".")).format(cut.suffix, cut.type)
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
        except CutEditorError as e:
            logging.warning(format(e))
            QtWidgets.QMessageBox.warning(self, "Validation error", format(e))
        else:
            super(CutEditorDialog, self).accept()

    @QtCore.pyqtSlot()
    def reject(self):
        """Overloaded slot for reject()."""
        super(CutEditorDialog, self).reject()


if __name__ == '__main__':
    import sys
    from tmEditor.core.Settings import CutSpecs
    logging.getLogger().setLevel(logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    menu = XmlDecoder.load('/home/arnold/xml/L1Menu_test_overlap_removal.xml')
    dialog = CutEditorDialog(menu)
    dialog.setupCuts(CutSpecs)
    from tmEditor.core.Algorithm import Cut
    cut = Cut(
        name="JET-SLICE_2to3",
        object=tmGrammar.JET,
        type=tmGrammar.SLICE,
        data="2,3",
        comment="NO one expects the spanish inquisition!"
    )
    # dialog.loadCut(cut)
    dialog.show()
    sys.exit(app.exec_())
