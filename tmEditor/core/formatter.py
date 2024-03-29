"""Various specialized string formatting functions."""

from typing import List

import tmGrammar

from .toolbox import listcompress
from .Settings import CutSpecs
from .types import FunctionCutTypes


def fHex(value: int) -> str:
    """Return pretty hex representation."""
    try:
        return "0x{0:x}".format(int(value))
    except ValueError:
        return ""


def fCompress(values: List[int]) -> str:
    """Return compressed representation of ranges of an integer list.
    >>> fCompress([0,1,2,3,5,7,8,9])
    '0-3, 5, 7-9'
    """
    tokens = []
    for pair in listcompress(values):
        if isinstance(pair, tuple):
            tokens.append("{0}-{1}".format(*pair))
        else:
            tokens.append(format(pair))
    return ", ".join(tokens)


def fFileSize(size) -> str:
    """Return human readable file size given in bytes.
    >>> fFileSize(1234)
    '1.2KiB'
    """
    suffix: str = "B"
    factor: int = 1024
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(size) < factor:
            return "{0:3.1f}{1}{2}".format(size, unit, suffix)
        size /= factor
    return "{0:.1f}{1}{2}".format(size, "Yi", suffix)


def fCutValue(value, precision: int = 3) -> str:
    """Return floating point representation for cut values in string format,
    returns empty string on error.
    """
    fmt = "+.{0}f".format(precision)
    try:
        return format(float(value), fmt)
    except ValueError:
        return ""


def fCutData(cut) -> str:
    """Return pretty formatted cut data according to cut specification settings."""
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
        elif cut.type == tmGrammar.MODEL:
            return "{0}".format(cut.data)
        else:
            entries = [entry.strip() for entry in cut.data.split(",")]
            # except isolation luts
            if cut.type == tmGrammar.ISO:
                return ", ".join([spec.data[entry] for entry in entries])
            return fCompress([int(entry) for entry in entries if entry.isdigit()])
    return cut.data


def fCutLabel(cut) -> str:
    """Formatted cut label containing name and values."""
    if cut.data:
        data = fCutData(cut)
        return "{0} ({1})".format(cut.name, data)
    elif cut.type in [tmGrammar.TBPT, tmGrammar.SCORE, tmGrammar.ASCORE, tmGrammar.CSCORE]:
        threshold = fCutValue(cut.minimum)
        return "{0} (>= {1})".format(cut.name, threshold)
    else:
        minimum = fCutValue(cut.minimum)
        maximum = fCutValue(cut.maximum)
        return "{0} [{1}, {2}]".format(cut.name, minimum, maximum)


def fCutLabelRichText(cut) -> str:
    """Rich text foramtted cut label, provided for convenience."""
    tokens = fCutLabel(cut).split()
    return "{0} {1}".format(tokens[0], " ".join(tokens[1:]))


def fThreshold(value: str) -> str:
    """Retrun formatted object requirement threshold.
    >>> fThreshold("2p5")
    '2.5 GeV'
    """
    value = format(value).replace("p", ".")  # Replace 'p' by comma.
    return "{:.1f} GeV".format(float(value))


def fCounts(value: str) -> str:
    """Retrun formatted object requirement count.
    >>> fCounts("42")
    '42 counts'
    """
    return "{:.0f} counts".format(float(value))


def fComparison(value: str) -> str:
    """Retrun formatted thresold comparisons signs.
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


def fBxOffset(value: int) -> str:
    """Return formatted BX offset, accepts strings or integers.
    >>> fBxOffset(2)
    '+2'
    """
    return "0" if int(value) == 0 else format(int(value), "+d")
