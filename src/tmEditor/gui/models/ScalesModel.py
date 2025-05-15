"""Scales model."""

from typing import Optional

from PySide6 import QtCore

import tmGrammar

from tmEditor.core.formatter import fCutValue
from .AbstractTableModel import AbstractTableModel

__all__ = ["ScalesModel"]

# HACK: overload with missing attributes.
tmGrammar.ET = "ET"
tmGrammar.PT = "PT"

kObject = "object"
kType = "type"
kMinimum = "minimum"
kMaximum = "maximum"
kStep = "step"
kNBits = "n_bits"


def fPatchType(item: dict[str, str]) -> str:
    """Patch muon type from ET to PT."""
    if item[kType] == tmGrammar.ET:
        if item[kObject] == tmGrammar.MU:
            return tmGrammar.PT
    return item[kType]


class ScalesModel(AbstractTableModel):
    """Default scales table model."""

    def __init__(self, menu, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(menu.scales.scales, parent)
        self.addColumnSpec("Object", lambda item: item[kObject])
        self.addColumnSpec("Type", fPatchType)
        self.addColumnSpec("Minimum", lambda item: item[kMinimum], format=fCutValue, textAlignment=self.AlignRight)
        self.addColumnSpec("Maximum", lambda item: item[kMaximum], format=fCutValue, textAlignment=self.AlignRight)
        self.addColumnSpec("Step", lambda item: item[kStep], format=fCutValue, textAlignment=self.AlignRight)
        self.addColumnSpec("Bitwidth", lambda item: item[kNBits], format=int, textAlignment=self.AlignRight)
        self.addEmptyColumn()
