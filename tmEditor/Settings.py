# -*- coding: utf-8 -*-
#
# TODO: reorganize
#

import tmGrammar
import sys, os

__all__ = ["cutSettings", ]

#
# Cut settings class
#

class CutSettings(object):
    """Cut specific settings."""

    def __init__(self, name, object, type, objects=None, range_precision=None,
                 range_step=None, range_unit=None, data=None, data_exclusive=False,
                 title=None, description=None, enabled=True):
        self.name = name
        self.object = object
        self.type = type
        self.objects = objects or []
        self.range_precision = int(range_precision or 0)
        self.range_step = float(range_step or 0.)
        self.range_unit = range_unit or ""
        self.data = data or {}
        self.data_exclusive = data_exclusive or False
        self.title = title or ""
        self.description = description or ""
        self.enabled = enabled

    @property
    def data_sorted(self):
        """Returns sorted list of data dict values."""
        return [self.data[key] for key in sorted(self.data.keys())]

cutSettings = [
    CutSettings(
        name="MU-ETA",
        object=tmGrammar.MU,
        type=tmGrammar.ETA,
        title="Muon eta",
        description="Restricts valid eta range for muon object requirement."
    ),
    CutSettings(
        name="MU-PHI",
        object=tmGrammar.MU,
        type=tmGrammar.PHI,
        range_unit="rad",
        title="Muon phi",
        description="Restricts valid phi range for muon object requirement."
    ),
    CutSettings(
        name="MU-QLTY",
        object=tmGrammar.MU,
        type=tmGrammar.QLTY,
        title="Muon quality",
        description="Applies quality filter for muon object requirement.",
        data={
          "0": "quality level 0",
          "1": "quality level 1",
          "2": "quality level 2",
          "3": "quality level 3",
          "4": "quality level 4",
          "5": "quality level 5",
          "6": "quality level 6",
          "7": "quality level 7",
          "8": "quality level 8",
          "9": "quality level 9",
          "10": "quality level 10",
          "11": "quality level 11",
          "12": "quality level 12",
          "13": "quality level 13",
          "14": "quality level 14",
          "15": "quality level 15"
      }
    ),
    CutSettings(
        name="MU-ISO",
        object=tmGrammar.MU,
        type=tmGrammar.ISO,
        title="Muon isolation",
        data={
          "0": "isolated",
          "1": "non-isolated",
          "2": "n/a",
          "3": "n/a"
      }
    ),
    CutSettings(
        name="MU-CHG",
        object=tmGrammar.MU,
        type=tmGrammar.CHG,
        title="Muon charge",
        data_exclusive=True,
        data={
          "positive": "positive",
          "negative": "negative"
      }
    ),
    CutSettings(
        name="EG-ETA",
        object=tmGrammar.EG,
        type=tmGrammar.ETA,
        title="Electron/gamma eta"
    ),
    CutSettings(
        name="EG-PHI",
        object=tmGrammar.EG,
        type=tmGrammar.PHI,
        range_unit="rad",
        title="Electron/gamma phi"
    ),
    CutSettings(
        enabled=False,
        name="EG-QLTY",
        object=tmGrammar.EG,
        type=tmGrammar.QLTY,
        title="Electron/gamma quality",
        data={
          "0": "quality level 0",
          "1": "quality level 1",
          "2": "quality level 2",
          "3": "quality level 3",
          "4": "quality level 4",
          "5": "quality level 5",
          "6": "quality level 6",
          "7": "quality level 7",
          "8": "quality level 8",
          "9": "quality level 9",
          "10": "quality level 10",
          "11": "quality level 11",
          "12": "quality level 12",
          "13": "quality level 13",
          "14": "quality level 14",
          "15": "quality level 15"
      }
    ),
    CutSettings(
        name="EG-ISO",
        object=tmGrammar.EG,
        type=tmGrammar.ISO,
        title="Electron/gamma isolation",
        data={
          "0": "isolated",
          "1": "non-isolated",
          "2": "n/a",
          "3": "n/a"
      }
    ),
    CutSettings(
        name="JET-ETA",
        object=tmGrammar.JET,
        type=tmGrammar.ETA,
        title="Jet eta"
    ),
    CutSettings(
        name="JET-PHI",
        object=tmGrammar.JET,
        type=tmGrammar.PHI,
        range_unit="rad",
        title="Jet phi"
    ),
    CutSettings(
        enabled=False,
        name="JET-QLTY",
        object=tmGrammar.JET,
        type=tmGrammar.QLTY,
        title="Jet quality",
        data={
          "0": "quality level 0",
          "1": "quality level 1",
          "2": "quality level 2",
          "3": "quality level 3",
          "4": "quality level 4",
          "5": "quality level 5",
          "6": "quality level 6",
          "7": "quality level 7",
          "8": "quality level 8",
          "9": "quality level 9",
          "10": "quality level 10",
          "11": "quality level 11",
          "12": "quality level 12",
          "13": "quality level 13",
          "14": "quality level 14",
          "15": "quality level 15"
      }
    ),
    CutSettings(
        name="TAU-ETA",
        object=tmGrammar.TAU,
        type=tmGrammar.ETA,
        title="Tau eta"
    ),
    CutSettings(
        name="TAU-PHI",
        object=tmGrammar.TAU,
        type=tmGrammar.PHI,
        range_unit="rad",
        title="Tau phi"
    ),
    CutSettings(
        enabled=False,
        name="TAU-QLTY",
        object=tmGrammar.TAU,
        type=tmGrammar.QLTY,
        title="Tau quality",
        data={
          "0": "quality level 0",
          "1": "quality level 1",
          "2": "quality level 2",
          "3": "quality level 3",
          "4": "quality level 4",
          "5": "quality level 5",
          "6": "quality level 6",
          "7": "quality level 7",
          "8": "quality level 8",
          "9": "quality level 9",
          "10": "quality level 10",
          "11": "quality level 11",
          "12": "quality level 12",
          "13": "quality level 13",
          "14": "quality level 14",
          "15": "quality level 15"
      }
    ),
    CutSettings(
        name="TAU-ISO",
        object=tmGrammar.TAU,
        type=tmGrammar.ISO,
        title="Tau isolation",
        data={
          "0": "isolated",
          "1": "non-isolated",
          "2": "n/a",
          "3": "n/a"
      }
    ),
    CutSettings(
        name="ETM-PHI",
        object=tmGrammar.ETM,
        type=tmGrammar.PHI,
        range_unit="rad",
        title="Missing energy phi"
    ),
    CutSettings(
        name="HTM-PHI",
        object=tmGrammar.HTM,
        type=tmGrammar.PHI,
        range_unit="rad",
        title="Missing energy phi"
    ),
    CutSettings(
        name="CHGCOR",
        object=tmGrammar.comb,
        type=tmGrammar.CHGCOR,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        title="Charge correlation",
        description="Applies charge correlation restriction to combination of two objects.\nExample: comb{MU20, MU20}[CHGCOR_OP]",
        data_exclusive=True,
        data={
          "ls": "like sign",
          "os": "opposite sign"
      }
    ),
    CutSettings(
        name="DETA",
        object=tmGrammar.dist,
        type=tmGrammar.DETA,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        range_precision=3,
        range_step=0.001,
        title="Delta eta",
        description="Applies delta eta restriction to combination of two objects."
    ),
    CutSettings(
        name="DPHI",
        object=tmGrammar.dist,
        type=tmGrammar.DPHI,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        range_precision=3,
        range_step=0.001,
        range_unit="rad",
        title="Delta phi",
        description="Applies delta phi restriction to combination of two objects."
    ),
    CutSettings(
        name="DR",
        object=tmGrammar.dist,
        type=tmGrammar.DR,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        range_precision=1,
        range_step=0.1,
        title="Delta-R",
        description="Applies delta-R restriction to combination of two objects.<br/><br/>&Delta;R = &radic;<span style=\"text-decoration:overline;\">&nbsp;&Delta;&eta;&sup2; + &Delta;&phi;&sup2;&nbsp;</span>"
    ),
    CutSettings(
        name="MASS",
        object=tmGrammar.mass,
        type=tmGrammar.MASS,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        range_precision=1,
        range_step=0.2,
        range_unit="GeV",
        title="Invariant mass",
        description="Applies invariant mass restriction to combination of two objects.<br/><br/>M = &radic;<span style=\"text-decoration:overline;\">&nbsp;2 <em>pt1</em> <em>pt2</em> (cosh(&Delta;&eta;) - cos(&Delta;&phi;))&nbsp;</span>"
    ),
]
