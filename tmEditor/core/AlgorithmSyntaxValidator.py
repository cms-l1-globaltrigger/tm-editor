"""Algorithm syntax validator class.

Usage example
-------------

>>> validator = AlgorithmSyntaxValidator(menu)
>>> validator.validate(expression)

"""

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List

import tmGrammar

from .Settings import CutSpecs
from .types import SignalTypes, ObjectScaleMap, FunctionTypes
from .Algorithm import isOperator, isObject, isExternal, isFunction
from .Algorithm import toObject, toExternal
from .Algorithm import functionObjects, functionCuts, functionObjectsCuts, objectCuts

__all__ = [
    "AlgorithmSyntaxValidator",
    "AlgorithmSyntaxError",
]

kMinimum = "minimum"
kMaximum = "maximum"
kName = "name"
kObject = "object"
kStep = "step"
kType = "type"


class SyntaxRule(ABC):
    """Base class to be inherited by custom syntax rule classes."""

    def __init__(self, validator) -> None:
        self.validator = validator

    def toObjectItem(self, token: str) -> tmGrammar.Object_Item:
        item = tmGrammar.Object_Item()
        if not tmGrammar.Object_parser(token, item):
            message = f"Invalid object statement {item.message!r}"
            raise AlgorithmSyntaxError(message, token)
        return item

    def toFunctionItem(self, token: str) -> tmGrammar.Function_Item:
        item = tmGrammar.Function_Item()
        if not tmGrammar.Function_parser(token, item):
            message = f"Invalid function statement {item.message!r}"
            raise AlgorithmSyntaxError(message, token)
        return item

    def toCutItem(self, token: str) -> tmGrammar.Cut_Item:
        item = tmGrammar.Cut_Item()
        if not tmGrammar.Cut_parser(token, item):
            message = f"Invalid cut statement {item.message!r} at object {token!r}"
            raise AlgorithmSyntaxError(message, token)
        return item

    @abstractmethod
    def validate(self, tokens: List[str]) -> None:
        ...


class SyntaxValidator:
    """Base class to be inherited by custom syntax validator classes."""

    def __init__(self, menu) -> None:
        self.menu = menu
        self.rules: List[SyntaxRule] = []

    def validate(self, expression: str) -> None:
        tokens: List[str] = self.tokenize(expression)
        for rule in self.rules:
            rule.validate(tokens)

    def addRule(self, cls) -> None:
        """Add a syntx rule class. Creates and tores an instance of the class."""
        self.rules.append(cls(self))

    def tokenize(self, expression: str) -> List[str]:
        """Parses algorithm expression and returns list of RPN tokens."""
        # Make sure to clear static algorithm logic.
        tmGrammar.Algorithm_Logic.clear()
        # Check for empty expression
        if not expression.strip():
            message = "Empty expression"
            raise AlgorithmSyntaxError(message)
        if not tmGrammar.Algorithm_parser(expression):
            message = f"Invalid expression {expression!r}"
            raise AlgorithmSyntaxError(message)
        return tmGrammar.Algorithm_Logic.getTokens()


class AlgorithmSyntaxError(Exception):
    """Exeption for algoithm syntax errors thrown by class AlgorithmSyntaxValidator."""
    def __init__(self, message, token=None):
        super().__init__(message)
        self.token = token


class AlgorithmSyntaxValidator(SyntaxValidator):
    """Algorithm syntax validator class."""

    def __init__(self, menu) -> None:
        super().__init__(menu)
        self.addRule(BasicSyntax)
        self.addRule(CombBxOffset)
        self.addRule(CombMultiThresholds)
        self.addRule(ChargeCorrelation)
        self.addRule(ObjectThresholds)
        self.addRule(RequiredObjectCuts)
        self.addRule(DistNrObjects)
        self.addRule(DistDeltaRange)
        self.addRule(CutCount)
        self.addRule(InvarientMass3)
        self.addRule(TransverseMass)
        self.addRule(TwoBodyPtNrObjects)
        self.addRule(ImpactPrameter)
        self.addRule(OverlapRemoval)


class BasicSyntax(SyntaxRule):
    """Validates basic algorithm syntax."""

    def validate(self, tokens: List[str]) -> None:
        menu = self.validator.menu
        ext_signal_names = [item[kName] for item in menu.extSignals.extSignals]
        for token in tokens:
            # Validate operators
            if isOperator(token):
                pass
            # Validate object
            elif isObject(token):
                o = self.toObjectItem(token)
                for cut in o.cuts:
                    self.toCutItem(cut)
            # Validate function
            elif isFunction(token):
                f = self.toFunctionItem(token)
                for cut in f.cuts:
                    self.toCutItem(cut)
            # Validate externals
            elif isExternal(token):
                external = toExternal(token)
                if external.signal_name not in ext_signal_names:
                    message = f"Invalid external signal {token!r}"
                    raise AlgorithmSyntaxError(message, token)
            else:
                message = f"Invalid expression {token!r}"
                raise AlgorithmSyntaxError(message, token)


class ObjectThresholds(SyntaxRule):
    """Validates object thresholds/counts."""

    def validate(self, tokens: List[str]) -> None:
        # TODO... better to use floating point representation and compare by string?!
        for token in tokens:
            # Validate object
            if isObject(token):
                object = toObject(token)
                if object.type not in SignalTypes:
                    self.validateThreshold(token, object)
            # Validate function
            if isFunction(token):
                for object in functionObjects(token):
                    self.validateThreshold(token, object)

    def validateThreshold(self, token: str, object):
        menu = self.validator.menu
        if object.type not in ObjectScaleMap:
            message = "Invalid object type {0!r}.".format(object.type)
            raise AlgorithmSyntaxError(message, token)
        scale = menu.scaleMeta(object, ObjectScaleMap[object.type])
        if not scale:
            message = "No such object type {0!r} in scale set {1!r}.".format(object.type, menu.scales.scaleSet[kName])
            raise AlgorithmSyntaxError(message, token)
        threshold = object.decodeThreshold()
        minimum = float(scale[kMinimum])
        maximum = float(scale[kMaximum])
        # step = float(scale[kStep])
        # Check range
        if not minimum <= threshold <= maximum:
            message = f"Object threshold exceeding scale limits ({minimum:.1f}..{maximum:.1f}) near {token!r}"
            raise AlgorithmSyntaxError(message, token)
        # Check step
        bins = menu.scaleBins(object, ObjectScaleMap[object.type])
        if not list(filter(lambda bin: float(bin[kMinimum]) == threshold or float(bin[kMaximum]) == threshold, bins)):
            message = f"Invalid threshold {object.threshold!r} at object {token!r}"
            raise AlgorithmSyntaxError(message, token)


class RequiredObjectCuts(SyntaxRule):

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if isObject(token):
                if token.startswith(tmGrammar.ADT):
                    o = self.toObjectItem(token)
                    ascore_count = 0
                    for cut in o.cuts:
                        if cut.startswith(tmGrammar.ADT + "-" + tmGrammar.ASCORE):
                            ascore_count += 1
                    if ascore_count != 1:
                        message = f"ADT object requires exactly one ASCORE cut. Invalid expression near {token!r}"
                        raise AlgorithmSyntaxError(message)
                #if token.startswith(tmGrammar.AXO):
                    #o = self.toObjectItem(token)
                    #ascore_count = 0
                    #for cut in o.cuts:
                        #if cut.startswith(tmGrammar.AXO + "-" + tmGrammar.SCORE):
                            #ascore_count += 1
                    #if ascore_count != 1:
                        #message = f"AXO object requires exactly one SCORE cut. Invalid expression near {token!r}"
                        #raise AlgorithmSyntaxError(message)
                if token.startswith(tmGrammar.AXO):
                    o = self.toObjectItem(token)
                    tcuts_count = 0
                    for cut in o.cuts:
                        if cut.startswith(tmGrammar.AXO + "-" + tmGrammar.SCORE):
                            tcuts_count += 1
                        if cut.startswith(tmGrammar.AXO + "-" + tmGrammar.MODEL):
                            tcuts_count += 1
                    if tcuts_count != 2:
                        message = f"AXO object requires exactly one SCORE and one MODEL cut. Invalid expression near {token!r}"
                        raise AlgorithmSyntaxError(message)
                if token.startswith(tmGrammar.TOPO):
                    o = self.toObjectItem(token)
                    tcuts_count = 0
                    for cut in o.cuts:
                        if cut.startswith(tmGrammar.TOPO + "-" + tmGrammar.SCORE):
                            tcuts_count += 1
                        if cut.startswith(tmGrammar.TOPO + "-" + tmGrammar.MODEL):
                            tcuts_count += 1
                    if tcuts_count != 2:
                        message = f"TOPO object requires exactly one SCORE and one MODEL cut. Invalid expression near {token!r}"
                        raise AlgorithmSyntaxError(message)
                if token.startswith(tmGrammar.CICADA):
                    o = self.toObjectItem(token)
                    cscore_count = 0
                    for cut in o.cuts:
                        if cut.startswith(tmGrammar.CICADA + "-" + tmGrammar.CSCORE):
                            cscore_count += 1
                    if cscore_count != 1:
                        message = f"CICADA object requires exactly one CSCORE cut. Invalid expression near {token!r}"
                        raise AlgorithmSyntaxError(message)


class CombBxOffset(SyntaxRule):
    """Validates that all objects of a combination function use the same BX offset."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            if name not in (tmGrammar.comb, tmGrammar.comb_orm):
                continue
            f = tmGrammar.Function_Item()
            if not tmGrammar.Function_parser(token, f):
                raise AlgorithmSyntaxError(f.message)
            objects = functionObjects(token)
            sameBxRange = len(objects)
            if name == tmGrammar.comb_orm:
                sameBxRange -= 1  # exclude last object
            for i in range(sameBxRange):
                if int(objects[i].bx_offset) != int(objects[0].bx_offset):
                    message = f"All object requirements of function {name}{{...}} must be of same bunch crossing offset.\n" \
                              f"Invalid expression near {token!r}"  # TODO differentiate!
                    raise AlgorithmSyntaxError(message, token)


class CombMultiThresholds(SyntaxRule):
    """Validates that all objects of a combination function with more then 4 objects require same thresholds."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            if name not in (tmGrammar.comb, ):
                continue
            f = tmGrammar.Function_Item()
            if not tmGrammar.Function_parser(token, f):
                raise AlgorithmSyntaxError(f.message)
            obj_tokens = []
            objects = []
            for obj_token in tmGrammar.Function_getObjects(f):
                if isObject(obj_token):
                    obj_tokens.append(obj_token)
                    objects.append(toObject(obj_token))
            if len(obj_tokens) <= 4:
                continue
            obj_cuts = functionObjectsCuts(token)
            thresholds = set()
            for i in range(len(objects)):
                if objects[i].type not in [tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU]:
                    message = f"All objects of function {name}{{...}} must be of type EG, JET or TAU.\n" \
                              f"Invalid expression near {obj_tokens[i]!r}"
                    raise AlgorithmSyntaxError(message, token)
                thresholds.add(objects[i].threshold)
                if len(thresholds) > 1:
                    message = f"All object thresholds of function {name}{{...}} must be identical, if assigning more then 4 objects.\n" \
                              f"Invalid expression near {obj_tokens[i]!r}"
                    raise AlgorithmSyntaxError(message, token)
                if obj_cuts[i]:
                    message = f"All objects of function {name}{{...}} must not use additioanl cuts, if assigning more then 4 objects.\n" \
                              f"Invalid expression near {obj_tokens[i]!r}"
                    raise AlgorithmSyntaxError(message, token)


class ChargeCorrelation(SyntaxRule):
    """Validates that all objects of a function are of type muon if applying a CHGCOR cut."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if not isFunction(token):
                continue
            f = tmGrammar.Function_Item()
            if not tmGrammar.Function_parser(token, f):
                raise AlgorithmSyntaxError(f.message)
            # Test for applied CHGCOR cuts
            if not list(filter(lambda name: name.startswith(tmGrammar.CHGCOR), functionCuts(token))):
                continue
            objects = functionObjects(token)
            for i in range(len(objects)):
                if objects[i].type != tmGrammar.MU:
                    name = token.split("{")[0]  # TODO: get function name
                    message = f"All object requirements of function {name}{{...}} must be of type {tmGrammar.MU!r} when applying a {tmGrammar.CHGCOR!r} cut.\n" \
                              f"Invalid expression near {token!r}"
                    raise AlgorithmSyntaxError(message, token)


class DistNrObjects(SyntaxRule):
    """Limit number of objects for distance function."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            if name not in (tmGrammar.dist, tmGrammar.dist_orm):
                continue
            f = tmGrammar.Function_Item()
            if not tmGrammar.Function_parser(token, f):
                raise AlgorithmSyntaxError(f.message)
            objects = functionObjects(token)
            if name == tmGrammar.dist and len(objects) != 2:
                message = f"Function {name}{{...}} requires excactly two object requirements.\n" \
                          f"Invalid expression near {token!r}"
                raise AlgorithmSyntaxError(message)


class DistDeltaRange(SyntaxRule):
    """Validates that delta-eta/phi cut ranges does not exceed assigned objects limits."""

    def validate(self, tokens: List[str]) -> None:
        menu = self.validator.menu
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            if name not in (tmGrammar.dist, tmGrammar.dist_orm):
                continue
            for name in functionCuts(token):
                cut = menu.cutByName(name)
                if cut.type == tmGrammar.DETA:
                    for object in functionObjects(token):
                        scale = list(filter(lambda scale: scale[kObject] == object.type and scale[kType] == tmGrammar.ETA, menu.scales.scales))[0]
                        minimum = 0
                        maximum = abs(float(scale[kMinimum])) + float(scale[kMaximum])
                        if not minimum <= float(cut.minimum) <= maximum:
                            message = f"Cut {name!r} minimum limit of {cut.minimum!r} exceed valid object DETA range of {minimum!r}"
                            raise AlgorithmSyntaxError(message)
                        if not minimum <= float(cut.maximum) <= maximum:
                            message = f"Cut {name!r} maximum limit of {cut.maximum!r} exceed valid object DETA range of {maximum!r}"
                            raise AlgorithmSyntaxError(message)
                if cut.type == tmGrammar.DPHI:
                    for object in functionObjects(token):
                        scale = list(filter(lambda scale: scale[kObject] == object.type and scale[kType] == tmGrammar.PHI, menu.scales.scales))[0]
                        minimum = 0
                        maximum = float(format(float(scale[kMaximum]), ".3f"))
                        if not minimum <= float(cut.minimum) <= maximum:
                            message = f"Cut {name!r} minimum limit of {cut.minimum!r} exceed valid object DPHI range of {minimum!r}"
                            raise AlgorithmSyntaxError(message)
                        if not minimum <= float(cut.maximum) <= maximum:
                            message = f"Cut {name!r} maximum limit of {cut.maximum!r} exceed valid object DPHI range of {maximum!r}"
                            raise AlgorithmSyntaxError(message)
                if cut.type == tmGrammar.DR:
                    pass  # TODO


class CutCount(SyntaxRule):
    """Limit number of cuts allowed to be assigned at once."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            # Objects
            if isObject(token):
                counts = self.countCuts(objectCuts(token))
                self.checkCutCount(token, counts)
            # Functions
            if isFunction(token):
                obj_cuts = functionObjectsCuts(token)
                for i, obj_token in enumerate(functionObjects(token)):
                    counts = self.countCuts(obj_cuts[i])
                    self.checkCutCount(token, counts)
                counts = self.countCuts(functionCuts(token))
                self.checkCutCount(token, counts)

    def countCuts(self, names: Iterable[str]) -> Dict:
        """Returns dictionary with key of cut object/type pair and occurence as value."""
        menu = self.validator.menu
        counts = {}
        for name in names:
            cut = menu.cutByName(name)
            if cut:
                key = (cut.object, cut.type)
                if key not in counts:
                    counts[key] = 0
                counts[key] += 1
        return counts

    def checkCutCount(self, token: str, counts: Dict) -> None:
        """Counts has to be a dictionary of format returned by countCuts()."""
        for key, count in counts.items():
            object_, type_ = key
            spec = (CutSpecs.query(enabled=True, object=object_, type=type_) or [None])[0]
            if spec:
                if count > spec.count_maximum:
                    name = key[1] if key[0] in FunctionTypes else "-".join(key)
                    message = f"In {token!r}, too many cuts of type {name!r} assigned, only {spec.count_maximum!r} allowed."
                    raise AlgorithmSyntaxError(message)


class TransverseMass(SyntaxRule):
    """Validates transverse mass object requirements At least one non eta object is required."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            if not name == tmGrammar.mass_trv:
                continue
            objects = functionObjects(token)
            nonEtaCount = 0
            for obj in objects:
                if obj.type in (tmGrammar.ETM, tmGrammar.ETMHF, tmGrammar.HTM, tmGrammar.HTMHF):
                    nonEtaCount += 1
            if nonEtaCount < 1:
                message = f"Transverse mass functions require at least one object requirement without an eta component (ETM, ETMHF, HTM, HTMHF).\n" \
                          f"Invalid expression near {token!r}"
                raise AlgorithmSyntaxError(message, token)


class InvarientMass3(SyntaxRule):
    """Validates invariant mass of three objects requirements."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            if not name == tmGrammar.mass_inv_3:
                continue
            objects = functionObjects(token)
            types = {object.type for object in objects}
            if len(types) != 1:
                message = f"Invariant mass for three objects functions require only muons or only calorimeter objects.\n" \
                          f"Invalid expression near {token!r}"
                raise AlgorithmSyntaxError(message, token)


class TwoBodyPtNrObjects(SyntaxRule):
    """Validates number of objects in combination with two body Pt cuts."""

    def validate(self, tokens: List[str]) -> None:
        menu = self.validator.menu
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            requiredObjects = (2, 2)
            if name in (tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm, tmGrammar.mass_trv_orm):
                requiredObjects = (2, 3)  # for overlap removal add the reference
            objects = functionObjects(token)
            for cutname in functionCuts(token):
                cut = menu.cutByName(cutname)
                if cut.type == tmGrammar.TBPT:
                    if not requiredObjects[0] <= len(objects) <= requiredObjects[1]:
                        message = f"Two body Pt cut requires exactly two base object requirements to be applied on.\n" \
                                  f"Invalid expression in function {name!r} with cut {cutname!r} near {token!r}"
                        raise AlgorithmSyntaxError(message, token)


class ImpactPrameter(SyntaxRule):
    """Impact parameter cut requires also a upt cut."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if isObject(token):
                item = self.toObjectItem(token)
                cuts = [cut for cut in item.cuts]
                self.validateObject(cuts, token)
            elif isFunction(token):
                for cuts in functionObjectsCuts(token):
                    self.validateObject(cuts, token)

    def hasImpactParameter(self, cuts) -> bool:
        for cut in cuts:
            if cut.startswith(tmGrammar.MU_IP):
                return True
        return False

    def hasUnconstrainedPt(self, cuts) -> bool:
        for cut in cuts:
            if cut.startswith(tmGrammar.MU_UPT):
                return True
        return False

    def validateObject(self, cuts, token: str) -> None:
        if self.hasImpactParameter(cuts):
            if not self.hasUnconstrainedPt(cuts):
                message: str = "Impact Parameter cut requires an Unconstrained Pt cut.\n" \
                               f"Invalid expression near {token!r}"
                raise AlgorithmSyntaxError(message, token)


class OverlapRemoval(SyntaxRule):
    """Validates only calorimeter objects are used with overlap removal functions."""

    def validate(self, tokens: List[str]) -> None:
        for token in tokens:
            if not isFunction(token):
                continue
            name = token.split("{")[0].strip()  # fetch function name, eg "dist{...}[...]"
            if name not in (tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm, tmGrammar.mass_trv_orm):
                continue
            objects = functionObjects(token)
            for object_ in objects:
                if object_.type not in (tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU):
                    message = "Overlap removal function supports only calorimeter type objects."
                    raise AlgorithmSyntaxError(message, token)
