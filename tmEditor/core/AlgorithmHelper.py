"""Algorithm helper."""

import re
from abc import ABC, abstractmethod
from typing import Any, Iterable, List, Optional

import tmGrammar

__all__ = [
    "join",
    "encode_comparison_operator",
    "encode_threshold",
    "decode_threshold",
    "encode_bx_offset",
    "encode_cuts",
    "ObjectHelper",
    "ExtSignalHelper",
    "FunctionHelper",
    "AlgorithmHelper",
]


def join(items: Iterable[Any], separator: Optional[str] = None) -> str:
    """Joins string representation of list items.
    >>> join(["foo", "bar", 42], "-")
    'foo-bar-42'
    """
    return (separator or "").join([format(item) for item in items])


def encode_comparison_operator(value: str) -> str:
    """Returns encoded comparison operator or an empty string on default value."""
    if value == tmGrammar.GE:
        return ""
    return value


def encode_threshold(value: float) -> str:
    """Returns encoded threshold value, omits comma if decimals are zero."""
    match = re.match(r"(\d+)(?:.(\d+))", format(float(value)))
    if match:
        integer, decimal = match.groups()
        if int(decimal):
            return "p".join([integer, decimal])
        return integer
    return ""


def decode_threshold(threshold: str) -> float:
    """Returns decoded float threshold."""
    return float(".".join(threshold.split("p")[:2]))  # TODO


def encode_bx_offset(value: int) -> str:
    """Returns encoded BX offset or an empty string on default value."""
    if value == 0:
        return ""
    return format(value, "+d")


def encode_cuts(items: Iterable[str]) -> str:
    """Returns encoded list of cuts or an empty string if no cuts."""
    s = join(items, ",")
    return "[{0}]".format(s) if s else s


class Helper(ABC):
    """Helper base class."""

    @abstractmethod
    def serialize(self) -> str:
        ...

    def __str__(self):
        return self.serialize()


class OperatorHelper(Helper):

    def __init__(self, operator: str) -> None:
        self.operator: str = operator

    def serialize(self) -> str:
        return f"{self.operator}"


class ObjectHelper(Helper):

    def __init__(self, type, threshold, bx_offset: int = 0, comparison_operator: Optional[str] = None, cuts=None) -> None:
        self.type = type
        self.comparison_operator = tmGrammar.GE if comparison_operator is None else comparison_operator
        self.threshold = threshold
        self.bx_offset: int = bx_offset
        self.cuts: List = cuts or []

    def addCut(self, cut) -> "ObjectHelper":
        self.cuts.append(cut)
        return self

    def serialize(self) -> str:
        comparison_operator = encode_comparison_operator(self.comparison_operator)
        threshold = encode_threshold(self.threshold)
        bx_offset = encode_bx_offset(self.bx_offset)
        cuts = encode_cuts(self.cuts)
        return f"{self.type}{comparison_operator}{threshold}{bx_offset}{cuts}"


class SignalHelper(Helper):

    def __init__(self, type, bx_offset: int = 0, cuts=None) -> None:
        self.type = type
        self.bx_offset: int = bx_offset
        self.cuts: List = cuts or []

    def addCut(self, cut) -> "SignalHelper":
        self.cuts.append(cut)
        return self

    def serialize(self) -> str:
        bx_offset = encode_bx_offset(self.bx_offset)
        cuts = encode_cuts(self.cuts)
        return f"{self.type}{bx_offset}{cuts}"


class ExtSignalHelper(Helper):

    def __init__(self, name: str, bx_offset: int = 0) -> None:
        self.name: str = name
        self.bx_offset: int = bx_offset
        if not name.startswith("EXT_"):
            raise ValueError(f"Invalid name for external signal: {name}")

    def serialize(self) -> str:
        bx_offset = encode_bx_offset(self.bx_offset)
        return f"{self.name}{bx_offset}"


class FunctionHelper(Helper):

    def __init__(self, name: str, objects=None, cuts=None) -> None:
        self.name: str = name
        self.objects: List = objects or []
        self.cuts: List = cuts or []

    def addObject(self, type: str, threshold: float, bx_offset: int = 0, comparison_operator: Optional[str] = None, cuts=None) -> ObjectHelper:
        comparison_operator = tmGrammar.GE if comparison_operator is None else comparison_operator
        helper = ObjectHelper(type, threshold, bx_offset, comparison_operator, cuts)
        self.objects.append(helper)
        return helper

    def addCut(self, cut) -> "FunctionHelper":
        self.cuts.append(cut)
        return self

    def serialize(self) -> str:
        objects = join(self.objects, ",")
        cuts = encode_cuts(self.cuts)
        return f"{self.name}{{{objects}}}{cuts}"


class AlgorithmHelper(Helper):

    def __init__(self, expression: Optional[List] = None) -> None:
        self.expression: List = expression or []

    def addOperator(self, operator: str) -> "AlgorithmHelper":
        helper = OperatorHelper(operator)
        self.expression.append(helper)
        return self

    def addObject(self, type: str, threshold: float, bx_offset: int = 0, comparison_operator: Optional[str] = None, cuts=None) -> ObjectHelper:
        comparison_operator = tmGrammar.GE if comparison_operator is None else comparison_operator
        helper = ObjectHelper(type, threshold, bx_offset, comparison_operator, cuts)
        self.expression.append(helper)
        return helper

    def addSignal(self, type: str, bx_offset: int = 0, cuts=None) -> SignalHelper:
        helper = SignalHelper(type, bx_offset, cuts)
        self.expression.append(helper)
        return helper

    def addExtSignal(self, name: str, bx_offset: int = 0) -> ExtSignalHelper:
        helper = ExtSignalHelper(name, bx_offset)
        self.expression.append(helper)
        return helper

    def addFunction(self, name: str, objects=None, cuts=None) -> FunctionHelper:
        helper = FunctionHelper(name, objects, cuts)
        self.expression.append(helper)
        return helper

    def serialize(self) -> str:
        return join(self.expression, " ")
