"""Cuts proxy model."""

from typing import Union

from PySide6 import QtCore

__all__ = ["CutsModelProxy"]


class CutsModelProxy(QtCore.QSortFilterProxyModel):
    """Custom cuts sort/filter proxy."""

    MinimumColumn: int = 3
    MaximumColumn: int = 4

    def lessThan(self, left: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex], right: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]) -> bool:
        """Custom cut sorting."""
        if left.column() in (self.MinimumColumn, self.MaximumColumn):
            return self._toFloat(left) < self._toFloat(right)
        return super().lessThan(left, right)

    def _toFloat(self, index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]) -> float:
        try:
            return float(self.sourceModel().data(index, QtCore.Qt.ItemDataRole.DisplayRole))
        except (TypeError, ValueError):
            return float("nan")
