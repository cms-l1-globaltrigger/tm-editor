# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Models
"""

from tmEditor.Toolbox import *
from tmEditor import AlgorithmFormatter

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from collections import namedtuple

__all__ = ['AlgorithmsModel', 'CutsModel', 'ObjectsModel', 'ExternalsModel',
    'BinsModel', 'ExtSignalsModel', ]

AlignLeft = Qt.AlignLeft | Qt.AlignVCenter
AlignRight = Qt.AlignRight | Qt.AlignVCenter
AlignCenter = Qt.AlignCenter | Qt.AlignVCenter

# ------------------------------------------------------------------------------
#  Base models
# ------------------------------------------------------------------------------

class BaseTableModel(QAbstractTableModel):
    """Abstract table model class to be inherited to display table data."""

    ColumnSpec = namedtuple('ColumnSpec', 'title, key, format, alignment, headerAlignment')

    def __init__(self, values, parent = None):
        super(BaseTableModel, self).__init__(parent)
        self.values = values
        self.columnSpecs = []

    def addColumnSpec(self, title, key, format = str, alignment = AlignLeft, headerAlignment = AlignCenter):
        spec = self.ColumnSpec(title, key, format, alignment, headerAlignment)
        self.columnSpecs.append(spec)
        return spec

    def rowCount(self, parent):
        return len(self.values)

    def columnCount(self, parent):
        return len(self.columnSpecs)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        row, column = index.row(), index.column()
        if role == Qt.DisplayRole:
            spec = self.columnSpecs[column]
            if spec.key not in self.values[row].keys():
                return QVariant()
            return spec.format(self.values[row][spec.key])
        if role == Qt.TextAlignmentRole:
            return self.columnSpecs[column].alignment
        return QVariant()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.columnSpecs[section].title
            if role == Qt.TextAlignmentRole:
                return self.columnSpecs[section].headerAlignment
        return QVariant()

# ------------------------------------------------------------------------------
#  Custom models
# ------------------------------------------------------------------------------

class AlgorithmsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(AlgorithmsModel, self).__init__(menu.algorithms, parent)
        self.formatter = AlgorithmFormatter()
        self.addColumnSpec("Index", 'index', int, AlignRight)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Expression", 'expression', fAlgorithm)
        # self.addColumnSpec("Comment", 'comment')

class CutsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(CutsModel, self).__init__(menu.cuts, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Object", 'object')
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
        self.addColumnSpec("Data", 'data')
        # self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'cut_id', int, AlignRight)

class ObjectsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ObjectsModel, self).__init__(menu.objects, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Type", 'type')
        self.addColumnSpec("Comparison", 'comparison_operator', fComparison, AlignRight)
        self.addColumnSpec("Threshold", 'threshold', fThreshold, AlignRight)
        self.addColumnSpec("BX Offset", 'bx_offset', fBxOffset, AlignRight)
        self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'object_id', int, AlignRight)

class ExternalsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ExternalsModel, self).__init__(menu.externals, parent)
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("BX Offset", 'bx_offset', fBxOffset, AlignRight)
        self.addColumnSpec("Comment", 'comment')
        self.addColumnSpec("Timestamp", 'datetime')
        self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'requirement_id', int, AlignRight, AlignRight)
        # self.addColumnSpec("ID2", 'ext_signal_id', int, AlignRight)

class BinsModel(BaseTableModel):

    def __init__(self, menu, name, parent = None):
        super(BinsModel, self).__init__(menu.scales.bins[name], parent)
        self.name = name
        self.addColumnSpec("Number dec", 'number', int, AlignRight)
        self.addColumnSpec("Number hex", 'number', fHex, AlignRight)
        self.addColumnSpec("Minimum", 'minimum', fCut, AlignRight)
        self.addColumnSpec("Maximum", 'maximum', fCut, AlignRight)
        self.addColumnSpec("Comment", 'comment')
        # self.addColumnSpec("ID", 'scale_id', int, AlignRight, AlignRight)

class ExtSignalsModel(BaseTableModel):

    def __init__(self, menu, parent = None):
        super(ExtSignalsModel, self).__init__(menu.extSignals.extSignals, parent)
        self.addColumnSpec("System", 'system')
        self.addColumnSpec("Name", 'name')
        self.addColumnSpec("Label", 'label')
        self.addColumnSpec("Cable", 'cable')
        self.addColumnSpec("Channel", 'channel')
        self.addColumnSpec("Description", 'description')
        # self.addColumnSpec("ID", 'ext_signal_id', int, AlignRight)
