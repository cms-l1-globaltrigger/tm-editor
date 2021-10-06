"""Algorithm container."""

import logging
import math
import re
from typing import List, Tuple

import tmGrammar

from .types import ObjectTypes, SignalTypes, ExternalObjectTypes, FunctionCutTypes
from .Settings import MaxAlgorithms
from .AlgorithmHelper import decode_threshold, encode_threshold

__all__ = ['Algorithm', ]

RegExObject = re.compile(r'({0})(?:\.(?:ge|eq)\.)?(\d+(?:p\d+)?)(?:[\+\-]\d+)?(?:\[[^\]]+\])?'.format(r'|'.join(ObjectTypes)))
"""Precompiled regular expression for matching object requirements."""

RegExSignal = re.compile(r'({0})(?:[\+\-]\d+)?'.format(r'|'.join(SignalTypes)))
"""Precompiled regular expression for matching signal requirements."""

RegExExtSignal = re.compile(r'{0}_[\w\d_\.]+(?:[\+\-]\d+)?'.format(r'|'.join(ExternalObjectTypes)))
"""Precompiled regular expression for matching external signal requirements."""

RegExFunction = re.compile(r'\w+\s*\{[^\}]+\}(?:\[[^\]]+\])?')
"""Precompiled regular expression for matching function expressions."""


def getObjectType(name: str) -> str:
    """Mapping object type enumeration to actual object names."""
    result = RegExObject.match(name)
    if result:
        objectType = result.group(1)
        if objectType in ObjectTypes:
            return objectType
    result = RegExSignal.match(name)
    if result:
        signalType = result.group(1)
        if signalType in SignalTypes:
            return signalType
    message = "invalid object/signal type `{0}`".format(name)
    raise RuntimeError(message)


def isOperator(token: str) -> bool:
    """Retruns True if token is an logical operator."""
    return tmGrammar.isGate(token)


def isObject(token: str) -> bool:
    """Retruns True if token is an object."""
    return tmGrammar.isObject(token) and not token.startswith(tmGrammar.EXT)


def isExternal(token: str) -> bool:
    """Retruns True if token is an external signal."""
    return tmGrammar.isObject(token) and token.startswith(tmGrammar.EXT)


def isCut(token: str) -> bool:
    """Retruns True if token is a cut."""
    return list(filter(lambda item: token.startswith(item), tmGrammar.cutName)) != []


def isFunction(token: str) -> bool:
    """Retruns True if token is a function."""
    return tmGrammar.isFunction(token)


def toObject(token: str) -> 'Object':
    """Returns an object's dict."""
    o = tmGrammar.Object_Item()
    if not tmGrammar.Object_parser(token, o):
        raise ValueError(token)
    return Object(
        name=o.getObjectName(),
        threshold=o.threshold,
        type=getObjectType(o.getObjectName()),
        comparison_operator=o.comparison,
        bx_offset=int(o.bx_offset)
    )


def toExternal(token: str) -> 'External':
    """Returns an external's dict."""
    # Test if external signal ends with bunch crossign offset.
    result = re.match(r'.*(\+\d+|\-\d+)$', token)
    bx_offset = result.group(1) if result else '+0'
    return External(
        name=token,
        bx_offset=int(bx_offset)
    )


def functionObjects(token: str) -> List['Object']:
    """Returns list of object dicts assigned to a function."""
    objects = []
    f = tmGrammar.Function_Item()
    if not tmGrammar.Function_parser(token, f):
        raise ValueError(token)
    for token in tmGrammar.Function_getObjects(f):
        if isObject(token):
            objects.append(toObject(token))
    return objects


def functionCuts(token: str) -> List:
    """Returns list of cut names assigned to a function."""
    cuts: List = []
    f = tmGrammar.Function_Item()
    if not tmGrammar.Function_parser(token, f):
        raise ValueError(token)
    for name in tmGrammar.Function_getCuts(f):
        cuts.append(name)
    return cuts


def functionObjectsCuts(token: str) -> List:
    """Returns lists of cuts assigned to function objects. Index ist object number.
    >>> functionObjectsCuts("comb{MU0[MU-QLTY_HQ,MU-ETA_2p1],MU0[MU-QLTY_OPEN]}")
    ['MU-QLTY_HQ,MU-ETA_2p1', 'MU-QLTY_OPEN']
    """
    cuts: List = []
    f = tmGrammar.Function_Item()
    if not tmGrammar.Function_parser(token, f):
        raise ValueError(token)
    # Note: returns strings containting list of cuts.
    for names in tmGrammar.Function_getObjectCuts(f):
        cuts.append(names.split(',') if names else [])
    return cuts


def objectCuts(token: str) -> List[str]:
    """Returns list of cut names assigned to an object."""
    o = tmGrammar.Object_Item()
    if not tmGrammar.Object_parser(token, o):
        raise ValueError(token)
    return list(o.cuts)


def calculateDRRange() -> Tuple[float, float]:
    """Calculate valid DR range. This is function is currently a prototype and
    should fetch the actual limits from the menus scales in future.
    dR = sqrt( dEta^2 + dPhi^2 )
    """
    dEta = 10.
    dPhi = math.pi
    minimum = 0.
    maximum = math.sqrt(math.pow(dEta, 2) + math.pow(dPhi, 2))
    return (minimum, maximum)


def calculateInvMassRange() -> Tuple[float, float]:
    """Calculate valid invariant mass range. This is function is currently a
    prototype and should fetch the actual limits from the menus scales in future.
    M = sqrt( 2 pt1 pt2 ( cosh(dEta) - cos(dPhi) )
    """
    pt1 = 1024.
    pt2 = 1024.
    dEta = 10.
    dPhi = math.pi
    minimum = 0.
    maximum = math.sqrt(2 * pt1 * pt2 * (math.cosh(dEta) - math.cos(dPhi)))
    return (minimum, maximum)


def calculateTwoBodyPtRange() -> Tuple[float, float]:
    """Calculate valid invariant mass range. This is function is currently a
    prototype and should fetch the actual limits from the menus scales in future.
    M = sqrt( pt1^2 + pt2^2 + 2pt1pt2 ( cos(dPhi)^2 + sin(dPhi)^2 )
    """
    pt1 = 2048.
    pt2 = 2048.
    dPhi = math.pi
    minimum = 0.
    maximum = math.sqrt(pt1**2 + pt2**2 + 2*pt1*pt2*(math.cos(dPhi)**2 + math.sin(dPhi)**2))
    return (minimum, maximum)


class Algorithm:
    """Algorithm container class."""

    RegExAlgorithmName = re.compile(r'^(L1_)([a-zA-Z\d_]+)$')

    def __init__(self, index: int, name: str, expression: str,
                 comment: str = None, labels: list = None):
        self.index: int = index
        self.name: str = name
        self.expression: str = expression
        self.comment: str = comment or ""
        self.labels: list = labels or []
        self.modified: bool = False

    def __eq__(self, item) -> bool:
        """Distinquish algorithms."""
        return (self.index, self.name, self.expression) == (item.index, item.name, item.expression)

    def __lt__(self, item) -> bool:
        """Custom sorting by index, name and expression."""
        return (self.index, self.name, self.expression) < (item.index, item.name, item.expression)

    def tokens(self) -> List[str]:
        """Returns list of RPN tokens of algorithm expression. Note that paranthesis is not included in RPN."""
        tmGrammar.Algorithm_Logic.clear()
        if not tmGrammar.Algorithm_parser(self.expression):
            raise ValueError("Failed to parse algorithm expression")
        return list(tmGrammar.Algorithm_Logic.getTokens())

    def objects(self) -> List[str]:
        """Returns list of object names used in the algorithm's expression."""
        objects = set()
        for token in self.tokens():
            if isObject(token):
                object = toObject(token) # Cast to object required to fetch complete name.
                if not object.name in objects:
                    objects.add(object.name)
            if isFunction(token):
                for object in functionObjects(token):
                    if not object.name in objects:
                        objects.add(object.name)
        return list(objects)

    def externals(self) -> List[str]:
        """Returns list of external names used in the algorithm's expression."""
        externals = set()
        for token in self.tokens():
            if isExternal(token):
                external = toExternal(token)
                if not external.name in externals:
                    externals.add(external.name)
        return list(externals)

    def cuts(self) -> List[str]:
        """Returns list of cut names used in the algorithm's expression."""
        cuts = set()
        for token in self.tokens():
            if isObject(token):
                for cut in objectCuts(token):
                    if not cut in cuts:
                        cuts.add(cut)
            if isFunction(token):
                for cut in functionCuts(token):
                    if not cut in cuts:
                        cuts.add(cut)
                for objcuts in functionObjectsCuts(token):
                    for cut in objcuts:
                        if not cut in cuts:
                            cuts.add(cut)
        return list(cuts)

    def validate(self) -> None:
        """Optional argument validate is a function to validate the algorithm expression."""

        if self.index >= MaxAlgorithms:
            message = f"algorithm index out of range: {self.index} : {self.name}"
            logging.error(message)
            raise ValueError(message)

        if not self.RegExAlgorithmName.match(self.name):
            message = f"invalid algorithm name: {self.index} : {self.name}"
            logging.error(message)
            raise ValueError(message)


class Cut:
    """Cut container class."""

    RegExCutName = re.compile(r'^([A-Z\-]+_)([a-zA-Z\d_]+)$')

    def __init__(self, name, object, type, minimum=None, maximum=None, data=None, comment=None):
        self.name = name
        self.object = object
        self.type = type
        self.minimum = minimum or 0. if not data else ""
        self.maximum = maximum or 0. if not data else ""
        self.data = data or ""
        self.comment = comment or ""
        self.modified = False

    @property
    def isFunctionCut(self) -> bool:
        return self.type in FunctionCutTypes

    @property
    def typename(self) -> str:
        if self.isFunctionCut:
            return self.type # HACK for function cuts
        return '-'.join([self.object, self.type])

    @property
    def suffix(self) -> str:
        return self.name[len(self.typename) + 1:] # TODO

    def __eq__(self, item) -> bool:
        """Distinquish cuts by it's uinque name."""
        return self.name == item.name

    def __lt__(self, item) -> bool:
        """Custom sorting by type and object and suffix name."""
        return (self.type, self.object, self.suffix) < (item.type, item.object, item.suffix)

    def scale(self, scale):
        if self.typename in scale.bins.keys():
            return scale.bins[self.typename]
        return None

    def validate(self) -> None:
        if not self.RegExCutName.match(self.name):
            message = f"invalid cut name: {self.name}"
            logging.error(message)
            raise ValueError(message)


class Object:
    """Object container class."""

    def __init__(self, name, type, threshold, comparison_operator=None, bx_offset=None, comment=None):
        self.name = name
        self.type = type
        self.threshold = threshold
        self.comparison_operator = comparison_operator or tmGrammar.GE
        self.bx_offset = bx_offset or 0
        self.comment = comment or ""

    def isSignal(self) -> bool:
        return self.type in SignalTypes

    def decodeThreshold(self) -> float:
        """Returns decoded threshold as float."""
        if self.isSignal():
            return 0
        return decode_threshold(self.threshold)

    def encodeThreshold(self, value: float):
        """Encode float to threshold, sets threshold."""
        self.threshold = encode_threshold(value)

    def __eq__(self, item) -> bool:
        """Distinquish objects."""
        return \
            (self.type, self.comparison_operator, self.decodeThreshold(), self.bx_offset) == \
            (item.type, item.comparison_operator, item.decodeThreshold(), item.bx_offset)

    def __lt__(self, item) -> bool:
        """Custom sorting by type, threshold and offset."""
        def sortable_type(type):
            if type in ObjectTypes:
                return ObjectTypes.index(type)
            return type
        return \
            (sortable_type(self.type), self.decodeThreshold(), self.bx_offset) < \
            (sortable_type(item.type), item.decodeThreshold(), item.bx_offset)

    def validate(self) -> None:
        pass


class External:
    """External container class."""

    RegExSignalName = re.compile(r"^(EXT_)([a-zA-Z\d\._]+)([+-]\d+)?$")

    def __init__(self, name, bx_offset=None, comment=None):
        self.name = name
        self.bx_offset = bx_offset or 0
        self.comment = comment or ""

    @property
    def basename(self) -> str:
        """Returns signal name with leading EXT_ prefix but without BX offset."""
        result = self.RegExSignalName.match(self.name)
        if result:
            return ''.join((result.group(1), result.group(2)))
        return self.name

    @property
    def signal_name(self) -> str:
        """Returns signal name without leading EXT_ prefix."""
        result = self.RegExSignalName.match(self.name)
        if result:
            return result.group(2)
        return self.name

    def __eq__(self, item) -> bool:
        """Distinquish objects."""
        return self.basename == item.basename and self.bx_offset == item.bx_offset

    def __lt__(self, item) -> bool:
        """Custom sorting by basename and offset."""
        return (self.basename, self.bx_offset) < (item.basename, item.bx_offset)

    def validate(self) -> None:
        if not self.RegExSignalName.match(self.name):
            message = f"invalid external signal name: {self.name}"
            logging.error(message)
            raise ValueError(message)
