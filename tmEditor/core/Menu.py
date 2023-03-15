"""Menu container."""

import logging
import uuid
import re
from typing import List, Optional

from distutils.version import StrictVersion

from .Settings import MaxAlgorithms
from .AlgorithmSyntaxValidator import AlgorithmSyntaxValidator
from .Algorithm import toObject, toExternal

__all__ = ["Menu", "GrammarVersion"]

GrammarVersion = StrictVersion("0.11")
"""Supported grammar version."""

kObject: str = "object"
kType: str = "type"


class Menu:
    """L1-Trigger Menu container class. Provides methods to read and write XML
    menu files and adding and removing contents.
    """

    def __init__(self) -> None:
        self.menu = MenuInfo()
        self.algorithms: List = []
        self.cuts: List = []
        self.objects: List = []
        self.externals: List = []
        self.scales = None
        self.extSignals = None

    def addObject(self, object) -> None:
        """Creates a new object by specifing its paramters and adds it to the menu. Provided for convenience."""
        self.objects.append(object)

    def addCut(self, cut) -> None:
        """Creates a new cut by specifing its paramters and adds it to the menu. Provided for convenience."""
        self.cuts.append(cut)

    def addExternal(self, external) -> None:
        """Creates a new external signal by specifing its paramters and adds it to the menu. Provided for convenience."""
        self.externals.append(external)

    def addAlgorithm(self, algorithm) -> None:
        """Creates a new algorithm by specifing its paramters and adds it to the menu. Provided for convenience.
        **Note:** related objects must be added separately to the menu.
        """
        self.algorithms.append(algorithm)

    def extendReferenced(self, algorithm) -> None:
        """Adds missing objects and external signals referenced by the
        *algorithm* to the menu.
        """
        # Add new objects to list.
        for item in algorithm.objects():
            if not self.objectByName(item):
                self.objects.append(toObject(item))
        # Add new external to list.
        for item in algorithm.externals():
            if not self.externalByName(item):
                self.externals.append(toExternal(item))

    def algorithmByName(self, name: str):
        """Returns algorithm item by its *name* or None if no such algorithm exists."""
        return (list(filter(lambda item: item.name == name, self.algorithms)) or [None])[0]

    def algorithmByIndex(self, index: int):
        """Returns algorithm item by its *index* or None if no such algorithm exists."""
        return (list(filter(lambda item: int(item.index) == int(index), self.algorithms)) or [None])[0]

    def algorithmsByObject(self, object):
        """Returns list of algorithms containing *object*."""
        return list(filter(lambda algorithm: object.name in algorithm.objects(), self.algorithms))

    def algorithmsByExternal(self, external):
        """Returns list of algorithms containing *external* signal."""
        return list(filter(lambda algorithm: external.basename in algorithm.externals(), self.algorithms))

    def objectByName(self, name: str):
        """Returns object requirement item by its *name* or None if no such object requirement exists."""
        return (list(filter(lambda item: item.name == name, self.objects)) or [None])[0]

    def cutByName(self, name: str):
        """Returns cut item by its *name* or None if no such cut exists."""
        return (list(filter(lambda item: item.name == name, self.cuts)) or [None])[0]

    def externalByName(self, name: str):
        """Returns external signal item by its *name* or None if no such external signal exists."""
        return (list(filter(lambda item: item.name == name, self.externals)) or [None])[0]

    def scaleMeta(self, object, scaleType):
        """Returns scale information for *object* by *scaleType*."""
        return (list(filter(lambda item: item[kObject] == object.type and item[kType] == scaleType, self.scales.scales)) or [None])[0]

    def scaleBins(self, object, scaleType):
        """Returns bins for *object* by *scaleType*."""
        key = f"{object.type}-{scaleType}"
        return self.scales.bins[key] if key in self.scales.bins else None

    def orphanedObjects(self) -> list:
        """Returns list of orphaned object names not referenced by any algorithm."""
        tags: list = [object.name for object in self.objects]
        for algorithm in self.algorithms:
            for name in algorithm.objects():
                if name in tags:
                    tags.remove(name)
        return tags

    def orphanedExternals(self) -> list:
        """Returns list of orphaned externals names not referenced by any algorithm."""
        tags: list = [external.name for external in self.externals]
        for algorithm in self.algorithms:
            for name in algorithm.objects():
                if name in tags:
                    tags.remove(name)
        return tags

    def orphanedCuts(self) -> list:
        """Returns list of orphaned cut names not referenced by any algorithm."""
        tags: list = [cut.name for cut in self.cuts]
        for algorithm in self.algorithms:
            for name in algorithm.cuts():
                if name in tags:
                    tags.remove(name)
        return tags

    def validate(self) -> None:
        """Consistecy check, raises exception in fail."""
        self.menu.validate()

        count = len(self.algorithms)
        if count > MaxAlgorithms:
            maximum = MaxAlgorithms
            message = f"exceeding maximum number of supported algorithms: {count} (maximum {maximum})"
            logging.error(message)
            raise ValueError(message)

        validate = AlgorithmSyntaxValidator(self).validate
        cutByName = self.cutByName
        objectByName = self.objectByName
        externalByName = self.externalByName

        for algorithm in self.algorithms:

            algorithm.validate()  # check params
            validate(algorithm.expression)  # validate expression

            for cut in algorithm.cuts():
                cutByName(cut).validate()

            for object in algorithm.objects():
                objectByName(object).validate()

            for external in algorithm.externals():
                externalByName(external).validate()


class MenuInfo:
    """Menu information container class."""

    RegExMenuName = re.compile(r"^(L1Menu_)([a-zA-Z0-9_]*)$")

    def __init__(self, name: Optional[str] = None, comment: Optional[str] = None):
        self.name: str = name or ""
        self.comment: str = comment or ""
        self.uuid_menu: str = ""
        self.grammar_version: str = ""

    def regenerate(self) -> None:
        """Regenerate menu UUID and update grammar version."""
        self.uuid_menu = format(uuid.uuid4())
        self.grammar_version = format(GrammarVersion)

    def validate(self) -> None:
        """Run consistency checks."""
        if not self.RegExMenuName.match(self.name):
            message = f"invalid menu name: `{self.name}' (must start with `L1Menu_' followed only by characters, numbers or underscores)"
            logging.error(message)
            raise ValueError(message)
