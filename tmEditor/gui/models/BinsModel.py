# -*- coding: utf-8 -*-

from tmEditor.core.formatter import fHex, fCutValue
from tmEditor.core.types import ThresholdCutNames
from .AbstractTableModel import AbstractTableModel

from PyQt5 import QtCore

__all__ = ['BinsModel', ]

kNumber = 'number'
kMinimum = 'minimum'
kMaximum = 'maximum'

# ------------------------------------------------------------------------------
#  Bins model class
# ------------------------------------------------------------------------------

class BinsModel(AbstractTableModel):
    """Default scale bins table model."""

    def __init__(self, menu, name, parent = None):
        super(BinsModel, self).__init__(menu.scales.bins[name], parent)
        self.name = name
        self.addColumnSpec("Number dec", lambda item: item[kNumber], int, self.AlignRight)
        self.addColumnSpec("Number hex", lambda item: item[kNumber], fHex, self.AlignRight)
        self.addColumnSpec("Minimum", lambda item: item[kMinimum], fCutValue, self.AlignRight)
        self.addColumnSpec("Maximum", self.maximumCallback, fCutValue, self.AlignRight)
        self.addEmptyColumn()
        # Calculate first and last bin sortd by maximum
        sortedBins = sorted(self.values, key=lambda item: float(item[kMaximum]))
        self.firstBin = sortedBins[0] if sortedBins else None
        self.lastBin = sortedBins[-1] if sortedBins else None

    def maximumCallback(self, item):
        """Custom infinite value for all ET/PT scales (visual adaption)."""
        if self.name in ThresholdCutNames:
            if item == self.lastBin:
                return float('inf')
        return item[kMaximum]
