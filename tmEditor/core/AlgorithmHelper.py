"""Algorithm helper."""

import re

import tmGrammar

__all__ = [
    'join',
    'encode_comparison_operator',
    'encode_threshold',
    'decode_threshold',
    'encode_bx_offset',
    'encode_cuts',
    'ObjectHelper',
    'ExtSignalHelper',
    'FunctionHelper',
    'AlgorithmHelper'
]


def join(items, separator=""):
    """Joins string representation of list items.
    >>> join(["foo", "bar", 42], "-")
    'foo-bar-42'
    """
    return separator.join([format(item) for item in items])


def encode_comparison_operator(value):
    """Returns encoded comparison operator or an empty string on default value."""
    if value == tmGrammar.GE:
        return ""
    return value


def encode_threshold(value, separator='p'):
    """Returns encoded threshold value, omits comma if decimals are zero."""
    integer, decimal = re.match(r'(\d+)(?:.(\d+))', format(float(value))).groups()
    if int(decimal):
        return separator.join([integer, decimal])
    return integer


def decode_threshold(threshold, separator='p'):
    """Returns decoded float threshold."""
    return float('.'.join(threshold.split(separator)[:2]))  # TODO


def encode_bx_offset(value):
    """Returns encoded BX offset or an empty string on default value."""
    if value == 0:
        return ""
    return format(value, '+d')


def encode_cuts(items):
    """Returns encoded list of cuts or an empty string if no cuts."""
    if not items:
        return ""
    return "[{0}]".format(join(items, ","))


class Helper:
    """Helper base class."""

    def serialize(self) -> str:
        raise NotImplementedError()

    def __str__(self):
        return self.serialize()


class ObjectHelper(Helper):

    def __init__(self, type, threshold, bx_offset=0, comparison_operator=tmGrammar.GE, cuts=None):
        self.type = type
        self.comparison_operator = comparison_operator
        self.threshold = threshold
        self.bx_offset = bx_offset
        self.cuts = cuts or []

    def addCut(self, cut):
        self.cuts.append(cut)
        return self

    def serialize(self) -> str:
        comparison_operator = encode_comparison_operator(self.comparison_operator)
        threshold = encode_threshold(self.threshold)
        bx_offset = encode_bx_offset(self.bx_offset)
        cuts = encode_cuts(self.cuts)
        return f"{self.type}{comparison_operator}{threshold}{bx_offset}{cuts}"


class SignalHelper(Helper):

    def __init__(self, type, bx_offset=0):
        self.type = type
        self.bx_offset = bx_offset

    def serialize(self) -> str:
        bx_offset = encode_bx_offset(self.bx_offset)
        return f"{self.type}{bx_offset}"


class ExtSignalHelper(Helper):

    def __init__(self, name, bx_offset=0):
        self.name = name
        self.bx_offset = bx_offset
        if not name.startswith("EXT_"):
            raise ValueError()

    def serialize(self) -> str:
        bx_offset = encode_bx_offset(self.bx_offset)
        return f"{self.name}{bx_offset}"


class FunctionHelper(Helper):

    def __init__(self, name, objects=None, cuts=None):
        self.name = name
        self.objects = objects or []
        self.cuts = cuts or []

    def addObject(self, type, threshold, bx_offset=0, comparison_operator=tmGrammar.GE, cuts=None):
        helper = ObjectHelper(type, threshold, bx_offset, comparison_operator, cuts)
        self.objects.append(helper)
        return helper

    def addCut(self, cut):
        self.cuts.append(cut)
        return self

    def serialize(self) -> str:
        objects = join(self.objects, ',')
        cuts = encode_cuts(self.cuts)
        return f"{self.name}{{{objects}}}{cuts}"


class AlgorithmHelper(Helper):

    def __init__(self, expression: list = None):
        self.expression: list = expression or []

    def addOperator(self, operator):
        self.expression.append(operator)
        return self

    def addObject(self, type, threshold, bx_offset=0, comparison_operator=tmGrammar.GE, cuts=None):
        helper = ObjectHelper(type, threshold, bx_offset, comparison_operator, cuts)
        self.expression.append(helper)
        return helper

    def addSignal(self, type, bx_offset=0):
        helper = SignalHelper(type, bx_offset)
        self.expression.append(helper)
        return helper

    def addExtSignal(self, name, bx_offset=0):
        helper = ExtSignalHelper(name, bx_offset)
        self.expression.append(helper)
        return helper

    def addFunction(self, name, objects=None, cuts=None):
        helper = FunctionHelper(name, objects, cuts)
        self.expression.append(helper)
        return helper

    def serialize(self) -> str:
        return join(self.expression, " ")
