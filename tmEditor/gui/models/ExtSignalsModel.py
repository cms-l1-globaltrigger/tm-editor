# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

from .AbstractTableModel import AbstractTableModel

from PyQt4 import QtCore
from PyQt4 import QtGui

from collections import namedtuple

__all__ = ['ExtSignalsModel', ]

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kSystem = 'system'
kName = 'name'
kLabel = 'label'
kCable = 'cable'
kChannel = 'channel'

def miniIcon(name):
    return QtGui.QIcon(":/icons/{name}.svg".format(name=name)).pixmap(13, 13)

# ------------------------------------------------------------------------------
#  External signals model class
# ------------------------------------------------------------------------------

class ExtSignalsModel(AbstractTableModel):
    """Default external signals table model."""

    def __init__(self, menu, parent = None):
        super(ExtSignalsModel, self).__init__(menu.extSignals.extSignals, parent)
        self.addColumnSpec("System", lambda item: item[kSystem])
        self.addColumnSpec("Name", lambda item: item[kName])
        self.addColumnSpec("Label", lambda item: item[kLabel] if kLabel in item else "")
        self.addColumnSpec("Cable", lambda item: item[kCable], int, self.AlignRight)
        self.addColumnSpec("Channel", lambda item: item[kChannel], int, self.AlignRight)
        self.addEmptyColumn()
