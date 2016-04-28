# -*- coding: utf-8 -*-

import json
import sys, os

__all__ = ["appSettings", "cutSettings", ]

#
# Constants
#

SETTINGS_FILENAME="settings.json"

#
# Helper functions
#

def readSettings():
    """Read settings from JSON side file."""
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), SETTINGS_FILENAME)
    with open(filename) as handle:
        kwargs = json.loads(handle.read())
    return kwargs

#
# Access functions
#

def appSettings():
    return AppSettings(**readSettings()['application'])

def cutSettings():
    return [CutSettings(**kwargs) for kwargs in readSettings()['cuts']]

#
# Abstract settings class
#

class Settings(object):
    """Settings container class."""

    def __init__(self, **kwargs):
        self.__registered = {}
        self.__required = []
        self.update(**kwargs)

    def add(self, key, default, fmt=str):
        assert key not in dir(Settings), "add(): reserved keword: {key}".format(key=key)
        assert key not in dir(self), "add(): key: {key} already registred".format(key=key)
        setattr(self, key, fmt(default) if fmt else default)
        self.__registered[key] = fmt

    def require(self, key, fmt=str):
        self.__required.append(key)
        self.add(key, None, fmt)

    def update(self, **kwargs):
        if not kwargs:
            return
        for key in self.__required:
            assert key in kwargs.keys(), "update(): requires key: {key} in {d} by {r}".format(key=key, d=kwargs, r=self.__required)
        for key, value in kwargs.items():
            assert key in self.__registered.keys(), "update(): no such key: {key} registered".format(key=key)
            fmt = self.__registered[key]
            setattr(self, key, fmt(value) if fmt else value)

    def items(self):
        return dict([(key, getattr(self, key)) for key in self.__registered.keys()])

    def __str__(self):
        return str(self.items())

#
# Cut settings class
#

class CutSettings(Settings):
    """Cut specific settings."""

    def __init__(self, **kwargs):
        super(CutSettings, self).__init__()
        self.add("enabled", True, bool)
        self.require("name")
        self.require("object")
        self.require("type")
        self.add("objects", [], None)
        self.add("range_precision", 0, int)
        self.add("range_step", 0, float)
        self.add("range_unit", "")
        self.add("data", {}, self.__intdict)
        self.add("data_exclusive", False, bool)
        self.add("title", "")
        self.add("description", "")
        self.update(**kwargs)

    @property
    def data_sorted(self):
        """Returns sorted list of data dict values. Keys are converted to integers."""
        return [self.data[key] for key in sorted(self.data.keys())]

    def __intdict(self, d):
        """Returns dictionary with keys converted to integers (assuming strings)."""
        return dict([(int(key), value) for key, value in d.items()])

#
# Unittests
#

if __name__ == "__main__":
    s = CutSettings()
    print s
    s.update(name=42, object='MU', type=422)
    print
    print s
    d = s.items()
    d.update(data={"0":"a", "1": "b"})
    print "d", d
    s.update(**d)
    print
    print s
    print
    spec = cutSettings()
    print spec
