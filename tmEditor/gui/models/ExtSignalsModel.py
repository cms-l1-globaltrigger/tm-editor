"""External signals model."""

from .AbstractTableModel import AbstractTableModel
from tmEditor.gui.CommonWidgets import miniIcon

__all__ = ['ExtSignalsModel', ]

# ------------------------------------------------------------------------------
#  Keys
# ------------------------------------------------------------------------------

kSystem = 'system'
kName = 'name'
kLabel = 'label'
kCable = 'cable'
kChannel = 'channel'

# ------------------------------------------------------------------------------
#  External signals model class
# ------------------------------------------------------------------------------

class ExtSignalsModel(AbstractTableModel):
    """Default external signals table model."""

    def __init__(self, menu, parent=None):
        super().__init__(menu.extSignals.extSignals, parent)
        self.addColumnSpec("System", lambda item: item[kSystem], decoration=miniIcon('ext'))
        self.addColumnSpec("Name", lambda item: item[kName])
        self.addColumnSpec("Label", lambda item: item[kLabel] if kLabel in item else "")
        self.addColumnSpec("Cable", lambda item: item[kCable], int, self.AlignRight)
        self.addColumnSpec("Channel", lambda item: item[kChannel], int, self.AlignRight)
        self.addEmptyColumn()
