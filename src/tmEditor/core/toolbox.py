"""Toolbox containing various helpers."""

import logging
import os
import platform
import re
import ssl
from typing import Dict, List, Optional, Tuple

from urllib.request import urlopen

from PyQt5 import QtCore

import tmTable

__all__ = [
    "getenv",
    "getXsdDir",
    "query",
    "natural_sort_key",
    "safe_str",
    "listextent",
    "listcompress",
    "decode_labels",
    "encode_labels",
    "CutSpecificationPool",
    "CutSpecification",
    "DownloadHelper"
]

# -----------------------------------------------------------------------------
#  Low level helper functions
# -----------------------------------------------------------------------------

def getenv(name: str) -> str:
    """Get environment variable. Raises a RuntimeError exception if variable not set."""
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"`{name}' environment not set")
    return value

def getXsdDir() -> str:
    """Returns path for XSD files."""
    return tmTable.UTM_XSD_DIR

def query(data: dict, **kwargs) -> list:
    """Perform dictionary query.
    >>> d = {"foo": 42, "bar": "baz"}
    >>> query(d, bar="baz")
    [{'bar': 'baz'}]
    """
    def lookup(entry, **kwargs):
        return sum([entry[key] == value for key, value in kwargs.items()])
    return list(filter(lambda entry: lookup(entry, **kwargs), data))

def natural_sort_key(s: str):
    """Natural string sorting.
    >>> sorted("100 10 3b 2 1".split(), key=natural_sort_key)
    ['1', '2', '3b', '10', '100']
    """
    _nsre = re.compile(r"([0-9]+)")
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, format(s))]

def safe_str(s: str, attrname: str) -> str:
    """Returns safe version of string. The function strips:
     * whitespaces, tabulators
     * newlines, carriage returns
     * NULL characters
    """
    t = s.strip(" \t\n\r\x00")
    if s != t:
        logging.warning("normalized %s: %r to %r", attrname, s, t)
    return t

def listextent(values: list):
    """Retruns extent of sorted list."""
    if values[0] == values[-1]:
        return values[0]
    return values[0], values[-1]

def listcompress(values: list):
    """Returns compressed ranges for sortel list."""
    ranges: list = []
    for value in values:
        if not ranges:
            ranges.append([value])
        elif value - ranges[-1][-1] > 1:
            ranges.append([value])
        else:
            ranges[-1].append(value)
    return [listextent(values) for values in ranges]

def decode_labels(s: str):
    """String to labels."""
    return sorted({label.strip() for label in s.split(",") if label.strip()})

def encode_labels(labels, pretty: bool = False):
    sep = ", " if pretty else ","
    return sep.join(sorted({label.strip() for label in labels if label.strip()}))

# -----------------------------------------------------------------------------
#  Cut settings class
# -----------------------------------------------------------------------------

class CutSpecificationPool:
    """Cut specification pool."""
    def __init__(self, *args) -> None:
        self.specs: Tuple = args

    def __len__(self) -> int:
        return len(self.specs)

    def __iter__(self):
        return iter(self.specs)

    def query(self, **kwargs) -> List:
        """Query specifications by attributes and values.
        >>> pool.filter(object="MU", type="ISO")
        [CutSpecification instance at 0x...>]
        """
        results: List = list(self.specs)
        for key, value in kwargs.items():
            results = list(filter(lambda spec: hasattr(spec, key) and getattr(spec, key) == value, results))
        return results

class CutSpecification:
    """Cut specific settings.
    name               full cut name (eg. "MU-QLTY_OPEN")
    object             cut object (eg. "MU") or function type (eg. "dist")
    type               cut type (eg. "QLTY")
    count              valid number of cuts of same type to be assigned at once, default is 1
    objects            optional list of allowed object types
    functions          optional list of allowed function types
    range_precision    used precision for range entries, default is 0
    range_step         single step for linear range entries, default is 0.
    range_unit         optional unit for range entries
    data               dictionary of valid data entries (value and name)
    data_exclusive     set data entries to be exclusive, default is false
    title              optional title of cut specification
    description        optional description of cut specification
    enabled            enable or disable cut specification, default is true
    """

    def __init__(self, name: str, object: str, type: str, count_minimum: int = 0,
                 count_maximum: int = 1, objects: Optional[List[str]] = None,
                 functions: Optional[List[str]] = None, range_precision: int = 0,
                 range_step: float = 0, range_unit: Optional[str] = None,
                 data: Optional[Dict] = None, data_exclusive: bool = False,
                 title: Optional[str] = None, description: Optional[str] = None,
                 enabled: bool = True):
        self.name: str = name
        self.object: str = object
        self.type: str = type
        self.count_maximum: int = count_maximum
        self.count_minimum: int = count_minimum
        self.objects: List[str] = objects or []
        self.functions: List[str] = functions or []
        self.range_precision: int = range_precision
        self.range_step: float = float(range_step)
        self.range_unit: str = range_unit or ""
        self.data: Dict = data or {}
        self.data_exclusive: bool = data_exclusive
        self.title: str = title or ""
        self.description: str = description or ""
        self.enabled: bool = enabled

    @property
    def data_sorted(self) -> List[str]:
        """Returns sorted list of data dict values."""
        return [self.data[key] for key in sorted(self.data.keys())]

    @staticmethod
    def join(object, type) -> str:
        """Join object and type tokens to build a combined cut name."""
        return "-".join((object, type))

# -----------------------------------------------------------------------------
#  Remote file downloader
# -----------------------------------------------------------------------------

class DownloadHelper(QtCore.QObject):
    """Simple download helper class, utilized to fetch remote XML files."""

    receivedChanged = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, fp, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__()
        self.fp = fp
        self.url = None
        self.contentLength: int = 0
        self.charset = None
        self.receivedSize: int = 0
        self.blockSize: int = 1024 * 128

    def urlopen(self, url, **kwargs):
        # Workaround for MacOS SSL verification bug (affects python from homebrew and macport).
        if platform.system() == "Darwin":
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            kwargs["context"] = ctx
        # Open remote URL
        self.url = urlopen(url, **kwargs)
        # Get byte size of remote content, either integer string or empty if not available.
        self.contentLength = int(self.url.info().get("Content-Length", 0)) or 0
        self.charset = self.url.info().get("charset", "utf-8")

    def __call__(self):
        """Use callback to update status while doenloading or return False to stop.
        """
        self.receivedSize = 0
        try:
            while True:
                buffer = self.url.read(self.blockSize)
                if not buffer:
                    break
                self.receivedSize += len(buffer)
                self.fp.write(buffer)  # TODO /breaks/ .decode(self.charset))
                self.receivedChanged.emit(self.receivedSize)
        finally:
            self.finished.emit()
