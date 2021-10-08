"""Toolbox containing various helpers."""

import logging
import os
import platform
import re
import ssl

from urllib.request import urlopen

import tmTable

__all__ = [
    'getenv',
    'getXsdDir',
    'query',
    'natural_sort_key',
    'safe_str',
    'listextent',
    'listcompress',
    'decode_labels',
    'encode_labels',
    'CutSpecificationPool',
    'CutSpecification',
    'DownloadHelper'
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
    >>> d = {'foo': 42, 'bar': 'baz'}
    >>> query(d, bar='baz')
    [{'bar': 'baz'}]
    """
    def lookup(entry, **kwargs):
        return sum([entry[key] == value for key, value in kwargs.items()])
    return list(filter(lambda entry: lookup(entry, **kwargs), data))

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """Natural string sorting.
    >>> sorted("100 10 3b 2 1".split(), key=natural_sort_key)
    ['1', '2', '3b', '10', '100']
    """
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
        logging.warning("normalized %s: '%s' to '%s'", attrname, s, t)
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
        if not ranges: ranges.append([value])
        elif value - ranges[-1][-1] > 1:
            ranges.append([value])
        else:
            ranges[-1].append(value)
    return [listextent(values) for values in ranges]

def decode_labels(s: str):
    """String to labels."""
    return sorted({label.strip() for label in s.split(',') if label.strip()})

def encode_labels(labels, pretty: bool = False):
    sep = ', ' if pretty else ','
    return sep.join(sorted({label.strip() for label in labels if label.strip()}))

# -----------------------------------------------------------------------------
#  Cut settings class
# -----------------------------------------------------------------------------

class CutSpecificationPool:
    """Cut specification pool."""
    def __init__(self, *args):
        self.specs: tuple = args

    def __len__(self) -> int:
        return len(self.specs)

    def __iter__(self):
        return iter(self.specs)

    def query(self, **kwargs):
        """Query specifications by attributes and values.
        >>> pool.filter(object='MU', type='ISO')
        [CutSpecification instance at 0x...>]
        """
        results: tuple = self.specs
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

    def __init__(self, name, object, type, count=None, objects=None, functions=None,
                 range_precision=None, range_step=None, range_unit=None,
                 data=None, data_exclusive=False, title=None, description=None,
                 enabled=True):
        self.name = name
        self.object = object
        self.type = type
        self.count = count or 1
        self.objects = objects or []
        self.functions = functions or []
        self.range_precision = int(range_precision or 0)
        self.range_step = float(range_step or 0.)
        self.range_unit = range_unit or ""
        self.data = data or {}
        self.data_exclusive = data_exclusive
        self.title = title or ""
        self.description = description or ""
        self.enabled = enabled

    @property
    def data_sorted(self):
        """Returns sorted list of data dict values."""
        return [self.data[key] for key in sorted(self.data.keys())]

    @staticmethod
    def join(object, type, separator='-'):
        """Join object and type tokens to build a combined cut name."""
        return separator.join((object, type))

# -----------------------------------------------------------------------------
#  Remote file downloader
# -----------------------------------------------------------------------------

class DownloadHelper:
    """Simple download helper class, utilized to fetch remote XML files."""

    def __init__(self):
        self.url = None
        self.contentLength = 0
        self.charset = None
        self.receivedSize = 0
        self.blockSize = 1024 * 10

    def urlopen(self, url, **kwargs):
        # Workaround for MacOS SSL verification bug (affects python from homebrew and macport).
        if platform.system() == 'Darwin':
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            kwargs['context'] = ctx
        # Open remote URL
        self.url = urlopen(url, **kwargs)
        # Get byte size of remote content, either integer string or empty if not available.
        self.contentLength = int(self.url.info().get('Content-Length', 0)) or 0
        self.charset = self.url.info().get('charset', 'utf-8')

    def get(self, fp, callback=None):
        """Use callback to update status while doenloading or return False to stop.
        """
        self.receivedSize = 0
        while True:
            buffer = self.url.read(self.blockSize)
            if not buffer:
                break
            self.receivedSize += len(buffer)
            fp.write(buffer) ## TODO /breaks/ .decode(self.charset))
            if callback:
                if not callback():
                    return
