"""Abstract table model."""

from typing import Any, Callable, Optional, Union

from collections import namedtuple

from PySide6 import QtCore

__all__ = ["AbstractTableModel"]

ColumnSpec = namedtuple("ColumnSpec", "title, callback, format, textAlignment, " \
                                        "decoration, headerToolTip, headerDecoration, " \
                                        "headerSizeHint, headerTextAlignment")


class AbstractTableModel(QtCore.QAbstractTableModel):
    """Abstract table model class to be inherited to display table data."""

    AlignLeft = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
    AlignRight = QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
    AlignCenter = QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter

    def __init__(self, values: list, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self.values: list = values
        self.columnSpecs: list[Optional[ColumnSpec]] = []

    def addColumnSpec(self, title: str, callback: Callable, *,
                      format=str,
                      textAlignment=AlignLeft,
                      decoration=None,
                      headerToolTip=None,
                      headerDecoration=None,
                      headerSizeHint=None,
                      headerTextAlignment=AlignCenter):
        """Add a column to be displayed, assign data using a callback (usually a lamda function accessing an attribute)."""
        spec = ColumnSpec(title, callback, format, textAlignment, decoration, headerToolTip, headerDecoration, headerSizeHint, headerTextAlignment)
        self.columnSpecs.append(spec)

    def addEmptyColumn(self) -> None:
        """Add an empty column. Can be used for appending empty space to small
        tables with view columns to prevent last column to get stretched."""
        self.columnSpecs.append(None)

    def toolTip(self, row, column) -> Optional[str]:
        """Reimplement this to provide data specific tool tip informations."""
        return None

    def rowCount(self, parent: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex] = QtCore.QModelIndex()) -> int:
        """Number of rows to be displayed."""
        return len(self.values)

    def columnCount(self, parent: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex] = QtCore.QModelIndex()) -> int:
        """Number of columns to be displayed."""
        return len(self.columnSpecs)

    def data(self, index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex], role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> object:
        """Returns cell specific data."""
        if not index.isValid():
            return None
        row, column = index.row(), index.column()
        spec = self.columnSpecs[column]
        if not spec:
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return spec.format(spec.callback(self.values[row])) # TODO
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            return int(spec.textAlignment)
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            return spec.decoration
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return self.toolTip(row, column)
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> object:
        """Returns header specific data."""
        spec = self.columnSpecs[section]
        if not spec:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return spec.title
            if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
                return int(spec.headerTextAlignment)
            if role == QtCore.Qt.ItemDataRole.DecorationRole:
                return spec.headerDecoration
            if role == QtCore.Qt.ItemDataRole.ToolTipRole:
                return spec.headerToolTip
            if role == QtCore.Qt.ItemDataRole.SizeHintRole:
                return spec.headerSizeHint
        return None
