"""Helper class for tmTable module."""

import tmTable


class TableHelper:

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        """Clear tables contents."""
        self.menu: tmTable.Menu = tmTable.Menu()
        self.scale: tmTable.Scale = tmTable.Scale()
        self.extSignal: tmTable.ExtSignal = tmTable.ExtSignal()

    def load(self, filename: str) -> str:
        """Load tables from XML file."""
        self.reset()
        filename = str(filename)  # fixing unicode bug
        return tmTable.xml2menu(filename, self.menu, self.scale, self.extSignal)

    def dump(self, filename: str) -> None:
        """Dump tables to XML file."""
        filename = str(filename)  # fixing unicode bug
        tmTable.menu2xml(self.menu, self.scale, self.extSignal, filename)
