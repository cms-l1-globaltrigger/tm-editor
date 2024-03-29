"""Algorithms model."""

from typing import Any, Optional

from PyQt5 import QtCore, QtGui

from tmEditor.core.toolbox import encode_labels
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from .AbstractTableModel import AbstractTableModel

__all__ = ["AlgorithmsModel"]

# ------------------------------------------------------------------------------
#  Algorithms model class
# ------------------------------------------------------------------------------

class AlgorithmsModel(AbstractTableModel):
    """Default algorithms table model."""

    def __init__(self, menu, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(menu.algorithms, parent)
        self.addColumnSpec("Index", lambda item: item.index, int, self.AlignRight)
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Expression", lambda item: item.expression, AlgorithmFormatter.normalize)
        self.addColumnSpec("Labels", lambda item: encode_labels(item.labels, pretty=True))

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> Any:
        """Overloaded for experimental decoration."""
        if index.isValid():
            if role == QtCore.Qt.FontRole:
                algorithm = self.values[index.row()]
                if algorithm.modified:
                    font = QtGui.QFont()
                    font.setWeight(QtGui.QFont.Bold)
                    return font
        return super().data(index, role)

    def insertRows(self, position: int, rows: int, parent: Optional[QtCore.QModelIndex] = None) -> bool:
        parent = QtCore.QModelIndex() if parent is None else parent
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.values.append(None)
        self.endInsertRows()
        return True

    def removeRows(self, position: int, rows: int, parent: Optional[QtCore.QModelIndex] = None) -> bool:
        parent = QtCore.QModelIndex() if parent is None else parent
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            algorithm = self.values[position + i]
            self.values.remove(algorithm)
        self.endRemoveRows()
        return True
