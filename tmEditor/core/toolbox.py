# -*- coding: utf-8 -*-

"""Toolbox containing various helpers.
"""

import tmGrammar

try:
    # Python 2
    from urllib2 import urlopen
    from urllib2 import URLError, HTTPError
except ImportError:
    # Python 3
    from urllib.request import urlopen
    from urllib.error import URLError, HTTPError

import re
import logging
import sys, os
import json
import platform
import ssl

# -----------------------------------------------------------------------------
#  Low level helper functions
# -----------------------------------------------------------------------------

def is_frozen():
    """Defined by PyInstaller, for bundled applications."""
    return getattr(sys, 'frozen', False)

def resource_path(relative):
    """Determine resource paths, when packed with PyInstaller"""
    bundle_dir = os.path.abspath(".")
    if is_frozen():
        bundle_dir = sys._MEIPASS
    return os.path.join(
        bundle_dir,
        relative
    )

def getenv(name):
    """Get environment variable. Raises a RuntimeError exception if variable not set."""
    value = os.getenv(name)
    if value is None:
        raise RuntimeError("`{name}' environment not set".format(**locals()))
    return value

def getRootDir():
    if is_frozen():
        return resource_path(".")
    return getenv('UTM_ROOT')

def getXsdDir():
    """Returns path for XSD files."""
    if is_frozen():
      return resource_path("xsd")
    try:
        return getenv('UTM_XSD_DIR')
    except RuntimeError:
        return os.path.join(getRootDir(), 'tmXsd')

def query(data, **kwargs):
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

def safe_str(s, attrname):
    """Returns safe version of string. The function strips:
     * whitespaces, tabulators
     * newlines, carriage returns
     * NULL characters
    """
    t = s.strip(" \t\n\r\x00")
    if s != t:
        logging.warning("normalized %s: '%s' to '%s'", attrname, s, t)
    return t

def listextent(values):
    """Retruns extent of sorted list."""
    if values[0] == values[-1]:
        return values[0]
    return values[0], values[-1]

def listcompress(values):
    """Returns compressed ranges for sortel list."""
    ranges=[]
    for value in values:
        if not ranges: ranges.append([value])
        elif value - ranges[-1][-1] > 1:
            ranges.append([value])
        else:
            ranges[-1].append(value)
    return [listextent(values) for values in ranges]

# -----------------------------------------------------------------------------
#  Cut settings class
# -----------------------------------------------------------------------------

class CutSpecificationPool(object):
    """Cut specification pool."""
    def __init__(self, *args):
        self.specs = args

    def __len__(self):
        return len(self.specs)

    def __iter__(self):
        return iter(self.specs)

    def query(self, **kwargs):
        """Query specifications by attributes and values.
        >>> pool.filter(object='MU', type='ISO')
        [CutSpecification instance at 0x...>]
        """
        results = self.specs
        for key, value in kwargs.iteritems():
            results = list(filter(lambda spec: hasattr(spec, key) and getattr(spec, key) == value, results))
        return results

class CutSpecification(object):
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

class DownloadHelper(object):
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
            ctx.verify_mode =ssl.CERT_NONE
            kwargs['context'] = ctx
        # Open remote URL
        self.url = urlopen(url, **kwargs)
        # Get byte size of remote content, either integer string or empty if not available.
        self.contentLength = int(self.url.info().get('Content-Length', 0)) or 0
        self.charset = self.url.info().get('charset', 'utf-8')

    def handleSSLVerificationError(self, e):
        """Workaround for MacOS SSL verification bug (affects python from homebrew and macport).
        Returns a SSL context on OS X and MacOS in case of an SSL verification error.
        """
        if "[SSL: CERTIFICATE_VERIFY_FAILED]" in e.reason:
            if platform.system() == 'Darwin':
                logging.warning("SSL verification failed for url: %s", url)
                logging.warning("This is a known bug on OS X and MacOS.")
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode =ssl.CERT_NONE
                return ctx
        raise

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
