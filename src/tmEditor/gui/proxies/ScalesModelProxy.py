"""Scales proxy model."""

from typing import Union

from PySide6 import QtCore

__all__ = ["ScalesModelProxy"]


class ScalesModelProxy(QtCore.QSortFilterProxyModel):
    """Custom cuts sort/filter proxy."""

    MinimumColumn: int = 2
    MaximumColumn: int = 3
    StepColumn: int = 4
    BitsColumn: int = 5

    def lessThan(self, left: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex], right: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]) -> bool:
        """Custom range sorting."""
        if left.column() in (self.MinimumColumn, self.MaximumColumn, self.StepColumn, self.BitsColumn):
            return self._toFloat(left) < self._toFloat(right)
        return super().lessThan(left, right)

    def _toFloat(self, index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]) -> float:
        try:
            return float(self.sourceModel().data(index, QtCore.Qt.ItemDataRole.DisplayRole))
        except (TypeError, ValueError):
            return float("nan")
