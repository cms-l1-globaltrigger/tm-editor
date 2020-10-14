"""Abstract table model."""

from collections import namedtuple

from PyQt5 import QtCore

__all__ = ['AbstractTableModel', ]

# ------------------------------------------------------------------------------
#  Abstract table model class
# ------------------------------------------------------------------------------

class AbstractTableModel(QtCore.QAbstractTableModel):
    """Abstract table model class to be inherited to display table data."""

    AlignLeft = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
    AlignRight = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
    AlignCenter = QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter

    ColumnSpec = namedtuple('ColumnSpec', 'title, callback, format, textAlignment, ' \
                                          'decoration, headerToolTip, headerDecoration, ' \
                                          'headerSizeHint, headerTextAlignment')

    def __init__(self, values, parent=None):
        super().__init__(parent)
        self.values = values
        self.columnSpecs = []

    def addColumnSpec(self, title, callback,
                      format=str,
                      textAlignment=AlignLeft,
                      decoration=QtCore.QVariant(),
                      headerToolTip=QtCore.QVariant(),
                      headerDecoration=QtCore.QVariant(),
                      headerSizeHint=QtCore.QVariant(),
                      headerTextAlignment=AlignCenter):
        """Add a column to be displayed, assign data using a callback (usually a lamda function accessing an attribute)."""
        spec = self.ColumnSpec(title, callback, format, textAlignment, decoration, headerToolTip, headerDecoration, headerSizeHint, headerTextAlignment)
        self.columnSpecs.append(spec)

    def addEmptyColumn(self):
        """Add an empty column. Can be used for appending empty space to small
        tables with view columns to prevent last column to get stretched."""
        self.columnSpecs.append(None)

    def toolTip(self, row, column):
        """Reimplement this to provide data specific tool tip informations."""
        return QtCore.QVariant()

    def rowCount(self, parent):
        """Number of rows to be displayed."""
        return len(self.values)

    def columnCount(self, parent):
        """Number of columns to be displayed."""
        return len(self.columnSpecs)

    def data(self, index, role):
        """Returns cell specific data."""
        if not index.isValid():
            return QtCore.QVariant()
        row, column = index.row(), index.column()
        spec = self.columnSpecs[column]
        if not spec:
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:
            return spec.format(spec.callback(self.values[row])) # TODO
        if role == QtCore.Qt.TextAlignmentRole:
            return spec.textAlignment
        if role == QtCore.Qt.DecorationRole:
            return spec.decoration
        if role == QtCore.Qt.ToolTipRole:
            return self.toolTip(row, column)
        return QtCore.QVariant()

    def headerData(self, section, orientation, role):
        """Returns header specific data."""
        spec = self.columnSpecs[section]
        if not spec:
            return QtCore.QVariant()
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return spec.title
            if role == QtCore.Qt.TextAlignmentRole:
                return spec.headerTextAlignment
            if role == QtCore.Qt.DecorationRole:
                return spec.headerDecoration
            if role == QtCore.Qt.ToolTipRole:
                return spec.headerToolTip
            if role == QtCore.Qt.SizeHintRole:
                return spec.headerSizeHint
        return QtCore.QVariant()
