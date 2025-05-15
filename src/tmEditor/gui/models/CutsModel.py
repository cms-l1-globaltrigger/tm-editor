"""Cuts model."""

from typing import Optional, Union

from PySide6 import QtCore, QtGui

import tmGrammar

from tmEditor.core.Settings import CutSpecs
from tmEditor.core.formatter import fCutValue, fCutData
from tmEditor.core.Algorithm import calculateDRRange
from tmEditor.core.Algorithm import calculateInvMassRange

from .AbstractTableModel import AbstractTableModel

__all__ = ["CutsModel"]


def maximumCallback(item):
    """Custom infinite value getter. Still a quick workaround."""
    if item.type == tmGrammar.MASS:
        spec = CutSpecs.query(type=item.type)[0]
        minimum, maximum = calculateInvMassRange()
        scale = spec.range_precision
        maximum = int(maximum * scale) / scale
        if item.maximum >= maximum:
            return float("inf")
    if item.type == tmGrammar.DR:
        spec = CutSpecs.query(type=item.type)[0]
        minimum, maximum = calculateDRRange()
        scale = spec.range_precision
        maximum = int(maximum * scale) / scale
        if item.maximum >= maximum: # HACK ...
            return float("inf")
    if item.type == tmGrammar.TBPT:
        # There is no maximum for TBPT
        return ""
    if (item.type == tmGrammar.SCORE) or (item.type == tmGrammar.CSCORE):
        # There is no maximum for SCORE and CSCORE
        return ""
    return item.maximum


class CutsModel(AbstractTableModel):
    """Default cuts table model."""

    def __init__(self, menu, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(menu.cuts, parent)
        self.menu = menu
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Type", lambda item: item.type)
        self.addColumnSpec("Minimum", lambda item: item.minimum, format=fCutValue, textAlignment=self.AlignRight)
        self.addColumnSpec("Maximum", maximumCallback, format=fCutValue, textAlignment=self.AlignRight)
        self.addColumnSpec("Data", lambda item: fCutData(item))

    def data(self, index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex], role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> object:
        """Overloaded for experimental icon decoration."""
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.FontRole:
                cut = self.values[index.row()]
                if cut.modified:
                    font = QtGui.QFont()
                    font.setWeight(QtGui.QFont.Weight.Bold)
                    return font
        return super().data(index, role)

    def insertRows(self, position: int, rows: int, parent: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex] = QtCore.QModelIndex()) -> bool:
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.values.append(None)
        self.endInsertRows()
        return True

    def removeRows(self, position: int, rows: int, parent: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex] = QtCore.QModelIndex()) -> bool:
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            value = self.values[position + i]
            self.values.remove(value)
        self.endRemoveRows()
        return True
