# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Data models for various tables.
"""

from tmEditor.Toolbox import *
from tmEditor import AlgorithmFormatter

from PyQt4 import QtCore
from PyQt4 import QtGui

from collections import namedtuple

__all__ = ['AlgorithmsModel', 'CutsModel', 'ObjectsModel', 'ExternalsModel',
    'ScalesModel', 'BinsModel', 'ExtSignalsModel', ]

AlignLeft = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
AlignRight = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
AlignCenter = QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter

def miniIcon(name):
    return QtGui.QIcon(":/icons/{name}.svg".format(name=name)).pixmap(13, 13)

# ------------------------------------------------------------------------------
#  Base models
# ------------------------------------------------------------------------------

class AbstractTableModel(QtCore.QAbstractTableModel):
    """Abstract table model class to be inherited to display table data."""

    ColumnSpec = namedtuple('ColumnSpec', 'title, callback, format, textAlignment, ' \
                                          'decoration, headerToolTip, headerDecoration, ' \
                                          'headerSizeHint, headerTextAlignment')

    def __init__(self, values, parent = None):
        super(AbstractTableModel, self).__init__(parent)
        self.values = values
        self.columnSpecs = []

    def addColumnSpec(self, title, callback, format=str, textAlignment=AlignLeft,
                      decoration=QtCore.QVariant(), headerToolTip=QtCore.QVariant(), headerDecoration=QtCore.QVariant(),
                      headerSizeHint=QtCore.QVariant(), headerTextAlignment=AlignCenter):
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

# ------------------------------------------------------------------------------
#  Custom models
# ------------------------------------------------------------------------------

class MenuModel(AbstractTableModel):
    """Default menu information model."""

    def __init__(self, menu, parent = None):
        super(CutsModel, self).__init__(menu.cuts, parent)
        self.menu = menu
        self.addColumnSpec("UUID", 'uuid_firmware')
        self.addColumnSpec("Grammar version", 'grammar_version')

class AlgorithmsModel(AbstractTableModel):
    """Default algorithms table model."""

    def __init__(self, menu, parent = None):
        super(AlgorithmsModel, self).__init__(menu.algorithms, parent)
        self.addColumnSpec("Index", lambda item: item.index, int, AlignRight)
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Expression", lambda item: item.expression, fAlgorithm)

    def insertRows(self, position, rows, parent = QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.values.append(None)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent = QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            algorithm = self.values[position + i]
            self.values.remove(algorithm)
        self.endRemoveRows()
        return True

class CutsModel(AbstractTableModel):
    """Default cuts table model."""

    def __init__(self, menu, parent = None):
        super(CutsModel, self).__init__(menu.cuts, parent)
        self.menu = menu
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Type", lambda item: item.type)
        self.addColumnSpec("Object", lambda item: item.object)
        self.addColumnSpec("Minimum", lambda item: item.minimum, fCut, AlignRight)
        self.addColumnSpec("Maximum", lambda item: item.maximum, fCut, AlignRight)
        self.addColumnSpec("Data", lambda item: item.data)

    # def data(self, index, role):
    #     """Overloaded for experimental icon decoration."""
    #     if index.isValid():
    #         if index.column() == 0:
    #             if role == QtCore.Qt.DecorationRole:
    #                 cut = self.values[index.row()]
    #                 return miniIcon(cut.type.lower())
    #     return super(CutsModel, self).data(index, role)

    def insertRows(self, position, rows, parent = QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.values.append(None)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent = QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            value = self.values[position + i]
            self.values.remove(value)
        self.endRemoveRows()
        return True

class ObjectsModel(AbstractTableModel):
    """Default object requirements table model."""

    def __init__(self, menu, parent = None):
        super(ObjectsModel, self).__init__(menu.objects, parent)
        self.addColumnSpec("Name", lambda item: item.name)
        self.addColumnSpec("Type", lambda item: item.type)
        self.addColumnSpec("", lambda item: item.comparison_operator, fComparison, headerToolTip="Comparison", headerDecoration=QtGui.QIcon(":/icons/compare.svg"), headerSizeHint=QtCore.QSize(26, -1))
        self.addColumnSpec("Threshold", lambda item: item.threshold, fThreshold, AlignRight)
        self.addColumnSpec("BX Offset", lambda item: item.bx_offset, fBxOffset, AlignRight)
        self.addEmptyColumn()

    def data(self, index, role):
        """Overloaded for experimental icon decoration."""
        if index.isValid():
            columnSpec = self.columnSpecs[index.column()]
            value = self.values[index.row()]
            if columnSpec:
                if columnSpec.title == "Name":
                    if role == QtCore.Qt.DecorationRole:
                        return miniIcon(value.type.lower())
                # Override display for count type objects (no decimals, no GeV suffix)
                if columnSpec.title == "Threshold":
                    if role == QtCore.Qt.DisplayRole:
                        if value.type in (tmGrammar.MBT0HFP, tmGrammar.MBT1HFP, tmGrammar.MBT0HFM, tmGrammar.MBT1HFM, tmGrammar.TOWERCOUNT):
                            return "{0:.0f} counts".format(float(value.threshold)) # return integer string!
        return super(ObjectsModel, self).data(index, role)

class ExternalsModel(AbstractTableModel):
    """Default external siganls requirements table model."""

    def __init__(self, menu, parent = None):
        super(ExternalsModel, self).__init__(menu.externals, parent)
        self.addColumnSpec("Name", lambda item: item.name, decoration=miniIcon('default'))
        self.addColumnSpec("BX Offset", lambda item: item.bx_offset, fBxOffset, AlignRight)
        self.addEmptyColumn()

class ScalesModel(AbstractTableModel):
    """Default scales table model."""

    def __init__(self, menu, parent = None):
        super(ScalesModel, self).__init__(menu.scales.scales, parent)
        self.addColumnSpec("Object", lambda item: item['object'])
        self.addColumnSpec("Type", lambda item: item['type'])
        self.addColumnSpec("Minimum", lambda item: item['minimum'], fCut, AlignRight)
        self.addColumnSpec("Maximum", lambda item: item['maximum'], fCut, AlignRight)
        self.addColumnSpec("Step", lambda item: item['step'], fCut, AlignRight)
        self.addColumnSpec("Bitwidth", lambda item: item['n_bits'], int, AlignRight)
        self.addEmptyColumn()

class BinsModel(AbstractTableModel):
    """Default scale bins table model."""

    def __init__(self, menu, name, parent = None):
        super(BinsModel, self).__init__(menu.scales.bins[name], parent)
        self.name = name
        self.addColumnSpec("Number dec", lambda item: item['number'], int, AlignRight)
        self.addColumnSpec("Number hex", lambda item: item['number'], fHex, AlignRight)
        self.addColumnSpec("Minimum", lambda item: item['minimum'], fCut, AlignRight)
        self.addColumnSpec("Maximum", lambda item: item['maximum'], fCut, AlignRight)
        self.addEmptyColumn()

class ExtSignalsModel(AbstractTableModel):
    """Default external signals table model."""

    def __init__(self, menu, parent = None):
        super(ExtSignalsModel, self).__init__(menu.extSignals.extSignals, parent)
        self.addColumnSpec("System", lambda item: item['system'])
        self.addColumnSpec("Name", lambda item: item['name'])
        self.addColumnSpec("Label", lambda item: item['label'] if 'label' in item else "")
        self.addColumnSpec("Cable", lambda item: item['cable'], int, AlignRight)
        self.addColumnSpec("Channel", lambda item: item['channel'], int, AlignRight)
        self.addEmptyColumn()
