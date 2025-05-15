"""Algorithms model."""

from typing import Any, Optional, Union

from PySide6 import QtCore, QtGui

from tmEditor.core.toolbox import encode_labels
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from .AbstractTableModel import AbstractTableModel

__all__ = ["AlgorithmsModel"]


class AlgorithmsModel(AbstractTableModel):
    """Default algorithms table model."""

    def __init__(self, menu, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(menu.algorithms, parent)
        self.addColumnSpec("Index", lambda item: item.index, format=int, textAlignment=self.AlignRight)
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Expression", lambda item: item.expression, format=AlgorithmFormatter.normalize)
        self.addColumnSpec("Labels", lambda item: encode_labels(item.labels, pretty=True))

    def data(self, index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex], role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        """Overloaded for experimental decoration."""
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.FontRole:
                algorithm = self.values[index.row()]
                if algorithm.modified:
                    font = QtGui.QFont()
                    font.setWeight(QtGui.QFont.Weight.Bold)
                    return font
        return super().data(index, role)

    def insertRows(self, position: int, rows: int, parent: Optional[Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]] = None) -> bool:
        parent = QtCore.QModelIndex() if parent is None else parent
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.values.append(None)
        self.endInsertRows()
        return True

    def removeRows(self, position: int, rows: int, parent: Optional[Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]] = None) -> bool:
        parent = QtCore.QModelIndex() if parent is None else parent
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            algorithm = self.values[position + i]
            self.values.remove(algorithm)
        self.endRemoveRows()
        return True
