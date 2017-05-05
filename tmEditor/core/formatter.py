# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Various specialized string formatting functions.
"""

from tmEditor.core.toolbox import listcompress
from tmEditor.core.Settings import CutSpecs
from tmEditor.core.AlgorithmFormatter import AlgorithmFormatter
from tmEditor.core.types import FunctionCutTypes

import tmGrammar

# -----------------------------------------------------------------------------
#  Common formatters
# -----------------------------------------------------------------------------

def fHex(value):
    """Returns pretty hex representation."""
    try:
        return '0x{0:x}'.format(int(value))
    except ValueError:
        return ''

def fCompress(values, separator=", ", dash="-"):
    """Returns compressed representation of ranges of an integer list.
    >>> fCompress([0,1,2,3,5,7,8,9])
    '0-3, 5, 7-9'
    """
    tokens = []
    for pair in listcompress(values):
        if isinstance(pair, tuple):
            tokens.append("{1}{0}{2}".format(dash, *pair))
        else:
            tokens.append(format(pair))
    return separator.join(tokens)

def fFileSize(size, suffix='B'):
    """Returns human readable file size given in bytes.
    >>> fFileSize(1234)
    '1.2KiB'
    """
    factor = 1024.
    for unit in ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'):
        if abs(size) < factor:
            return "{0:3.1f}{1}{2}".format(size, unit, suffix)
        size /= factor
    return "{0:.1f}{1}{2}".format(size, 'Yi', suffix)

# -----------------------------------------------------------------------------
#  Formatters for cuts
# -----------------------------------------------------------------------------

def fCutValue(value, precision=3):
    """Returns floating point representation for cut values in string format,
    returns empty string on error.
    """
    fmt = '+.{0}f'.format(precision)
    try:
        return format(float(value), fmt)
    except ValueError:
        return ''

def fCutData(cut, separator=", "):
    """Returns pretty formatted cut data according to cut specification settings."""
    if cut.type in FunctionCutTypes:
        spec = (CutSpecs.query(type=cut.type) or [None])[0]
    else:
        spec = (CutSpecs.query(object=cut.object, type=cut.type) or [None])[0]
    if spec:
        # Translate exclusive entries in a more human readable way
        if spec.data_exclusive:
            return spec.data[cut.data.strip()]
        elif cut.type == tmGrammar.SLICE:
            if cut.minimum == cut.maximum:
                return "[{0}]".format(int(cut.minimum))
            else:
                return "[{0}-{1}]".format(int(cut.minimum), int(cut.maximum))
        else:
            entries = [entry.strip() for entry in cut.data.split(",")]
            if cut.type == tmGrammar.ISO: # except isolation luts
                return ", ".join([spec.data[entry] for entry in entries])
            return fCompress([int(entry) for entry in entries if entry.isdigit()])
    return cut.data

# -----------------------------------------------------------------------------
#  Formatters for object requirements
# -----------------------------------------------------------------------------

def fThreshold(value, suffix=" GeV"):
    """Retruns formatted object requirement threshold.
    >>> fThreshold("2p5")
    '2.5 GeV'
    """
    value = format(value).replace('p', '.') # Replace 'p' by comma.
    return "{0:.1f}{1}".format(float(value), suffix)

def fCounts(value, suffix=" counts"):
    """Retruns formatted object requirement count.
    >>> fCounts("42")
    '42 counts'
    """
    return "{0:.0f} counts".format(float(value), suffix)

def fComparison(value):
    """Retruns formatted thresold comparisons signs.
    >>> fComparison(tmGrammar.GE)
    '>='
    """
    return {
        tmGrammar.EQ: "==",
        tmGrammar.GE: ">=",
        tmGrammar.GT: ">",
        tmGrammar.LE: "<=",
        tmGrammar.LT: "<",
        tmGrammar.NE: "!=",
    }[value]

def fBxOffset(value):
    """Retruns formatted BX offset, accepts strings or integers.
    >>> fBxOffset(2)
    '+2'
    """
    return '0' if int(value) == 0 else format(int(value), '+d')
