"""Scales model."""

from typing import Optional

from PyQt5 import QtCore

import tmGrammar

from tmEditor.core.formatter import fCutValue
from .AbstractTableModel import AbstractTableModel

__all__ = ['ScalesModel', ]

# HACK: overload with missing attributes.
tmGrammar.ET = "ET"
tmGrammar.PT = "PT"

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kObject = 'object'
kType = 'type'
kMinimum = 'minimum'
kMaximum = 'maximum'
kStep = 'step'
kNBits = 'n_bits'

def fPatchType(item):
    """Patch muon type from ET to PT."""
    if item[kType] == tmGrammar.ET:
        if item[kObject] == tmGrammar.MU:
            return tmGrammar.PT
    return item[kType]

# ------------------------------------------------------------------------------
#  Scales model class
# ------------------------------------------------------------------------------

class ScalesModel(AbstractTableModel):
    """Default scales table model."""

    def __init__(self, menu, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(menu.scales.scales, parent)
        self.addColumnSpec("Object", lambda item: item[kObject])
        self.addColumnSpec("Type", fPatchType)
        self.addColumnSpec("Minimum", lambda item: item[kMinimum], fCutValue, self.AlignRight)
        self.addColumnSpec("Maximum", lambda item: item[kMaximum], fCutValue, self.AlignRight)
        self.addColumnSpec("Step", lambda item: item[kStep], fCutValue, self.AlignRight)
        self.addColumnSpec("Bitwidth", lambda item: item[kNBits], int, self.AlignRight)
        self.addEmptyColumn()
