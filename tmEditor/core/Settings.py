# -*- coding: utf-8 -*-
#

from tmEditor.core.toolbox import CutSpecificationPool, CutSpecification

import tmGrammar
import sys, os

__all__ = ['MaxAlgorithms', 'CutSpecs', ]

MaxAlgorithms = 512
"""Maximum number of supported algorithms."""

VersionUrl = "https://svnweb.cern.ch/trac/cactus/export/HEAD/trunk/cactusprojects/ugt/menu/version.json"
"""Server side version and scale set information URL."""

DefaultScaleSetUri = "scales/L1Menu_{scale_set}.xml"
"""Default URI format string for server side scale set XML files."""

DefaultExtSignalSetUri = "cabling/L1Menu_{ext_signal_set}.xml"
"""Default URI format string for server side external signal set XML files."""

DownloadSite = "http://globaltrigger.hephy.at/upgrade/tme/downloads"
"""Web site providing download information."""

CutSpecs = CutSpecificationPool(
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.ETA),
        object=tmGrammar.MU,
        type=tmGrammar.ETA,
        count=2,
        title="Muon eta",
        description="Restricts valid eta range for muon object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.PHI),
        object=tmGrammar.MU,
        type=tmGrammar.PHI,
        count=2,
        range_unit="rad",
        title="Muon phi",
        description="Restricts valid phi range for muon object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.QLTY),
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
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.ISO),
        object=tmGrammar.MU,
        type=tmGrammar.ISO,
        title="Muon isolation",
        description="",
        data={
          "0": "isolated",
          "1": "non-isolated",
          "2": "n/a",
          "3": "n/a"
        }
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.CHG),
        object=tmGrammar.MU,
        type=tmGrammar.CHG,
        title="Muon charge",
        description="<strong>Example:</strong> <pre>MU20[MU-CHG_NEG]</pre>",
        data_exclusive=True,
        data={
          "positive": "positive",
          "negative": "negative"
        }
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.SLICE),
        object=tmGrammar.MU,
        type=tmGrammar.SLICE,
        range_precision=0,
        range_step=1,
        title="Muon slice",
        description="Restricts collection range for muon object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.EG, tmGrammar.ETA),
        object=tmGrammar.EG,
        type=tmGrammar.ETA,
        count=2,
        title="Electron/gamma eta",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.EG, tmGrammar.PHI),
        object=tmGrammar.EG,
        type=tmGrammar.PHI,
        count=2,
        range_unit="rad",
        title="Electron/gamma phi",
        description=""
    ),
    CutSpecification(
        enabled=False,
        name=CutSpecification.join(tmGrammar.EG, tmGrammar.QLTY),
        object=tmGrammar.EG,
        type=tmGrammar.QLTY,
        title="Electron/gamma quality",
        description="",
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
    CutSpecification(
        name=CutSpecification.join(tmGrammar.EG, tmGrammar.ISO),
        object=tmGrammar.EG,
        type=tmGrammar.ISO,
        title="Electron/gamma isolation",
        description="",
        data={
          "0": "isolated",
          "1": "non-isolated",
          "2": "n/a",
          "3": "n/a"
        }
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.EG, tmGrammar.SLICE),
        object=tmGrammar.EG,
        type=tmGrammar.SLICE,
        title="Electron/gamma slice",
        description="Restricts collection range for electron/gamma object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.JET, tmGrammar.ETA),
        object=tmGrammar.JET,
        type=tmGrammar.ETA,
        count=2,
        title="Jet eta",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.JET, tmGrammar.PHI),
        object=tmGrammar.JET,
        type=tmGrammar.PHI,
        count=2,
        range_unit="rad",
        title="Jet phi",
        description=""
    ),
    CutSpecification(
        enabled=False,
        name=CutSpecification.join(tmGrammar.JET, tmGrammar.QLTY),
        object=tmGrammar.JET,
        type=tmGrammar.QLTY,
        title="Jet quality",
        description="",
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
    CutSpecification(
        name=CutSpecification.join(tmGrammar.JET, tmGrammar.SLICE),
        object=tmGrammar.JET,
        type=tmGrammar.SLICE,
        title="Jet slice",
        description="Restricts collection range for jet object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.TAU, tmGrammar.ETA),
        object=tmGrammar.TAU,
        type=tmGrammar.ETA,
        count=2,
        title="Tau eta",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.TAU, tmGrammar.PHI),
        object=tmGrammar.TAU,
        type=tmGrammar.PHI,
        count=2,
        range_unit="rad",
        title="Tau phi",
        description=""
    ),
    CutSpecification(
        enabled=False,
        name=CutSpecification.join(tmGrammar.TAU, tmGrammar.QLTY),
        object=tmGrammar.TAU,
        type=tmGrammar.QLTY,
        title="Tau quality",
        description="",
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
    CutSpecification(
        name=CutSpecification.join(tmGrammar.TAU, tmGrammar.ISO),
        object=tmGrammar.TAU,
        type=tmGrammar.ISO,
        title="Tau isolation",
        description="",
        data={
          "0": "isolated",
          "1": "non-isolated",
          "2": "n/a",
          "3": "n/a"
        }
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.TAU, tmGrammar.SLICE),
        object=tmGrammar.TAU,
        type=tmGrammar.SLICE,
        title="Tau slice",
        description="Restricts collection range for tau object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.ETM, tmGrammar.PHI),
        object=tmGrammar.ETM,
        type=tmGrammar.PHI,
        count=2,
        range_unit="rad",
        title="Missing energy phi",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.ETMHF, tmGrammar.PHI),
        object=tmGrammar.ETMHF,
        type=tmGrammar.PHI,
        count=2,
        range_unit="rad",
        title="Missing energy HF phi",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.HTM, tmGrammar.PHI),
        object=tmGrammar.HTM,
        type=tmGrammar.PHI,
        count=2,
        range_unit="rad",
        title="Missing energy phi",
        description=""
    ),
    CutSpecification(
        name=tmGrammar.CHGCOR,
        object=tmGrammar.comb,
        type=tmGrammar.CHGCOR,
        objects=[tmGrammar.MU],
        functions=[tmGrammar.comb, tmGrammar.dist, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_trv],
        title="Charge correlation",
        description="Applies charge correlation restriction to combinations of two or more muon objects. It can be applied to functions comb, dist, mass_inv and mass_trv.<br/><br/>" \
                    "<strong>Example:</strong> <pre>comb{MU20, MU20}[CHGCOR_OS]</pre>",
        data_exclusive=True,
        data={
          "ls": "like sign",
          "os": "opposite sign"
        }
    ),
    CutSpecification(
        name=tmGrammar.DETA,
        object=tmGrammar.dist,
        type=tmGrammar.DETA,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_orm, tmGrammar.mass_trv, tmGrammar.mass_trv_orm],
        range_precision=3,
        range_step=0.001,
        title="Delta eta",
        description="Applies delta eta restriction to combination of two objects.<br/><br/>" \
                    "<strong>Example:</strong> <pre>dist{MU20, MU20}[DETA_SAMPLE]</pre>"
    ),
    CutSpecification(
        name=tmGrammar.DPHI,
        object=tmGrammar.dist,
        type=tmGrammar.DPHI,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_orm, tmGrammar.mass_trv, tmGrammar.mass_trv_orm],
        range_precision=3,
        range_step=0.001,
        range_unit="rad",
        title="Delta phi",
        description="Applies delta phi restriction to combination of two objects.<br/><br/>" \
                    "<strong>Example:</strong> <pre>dist{MU20, MU20}[DPHI_SAMPLE]</pre>"
    ),
    CutSpecification(
        name=tmGrammar.DR,
        object=tmGrammar.dist,
        type=tmGrammar.DR,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_orm, tmGrammar.mass_trv, tmGrammar.mass_trv_orm],
        range_precision=1,
        range_step=0.1,
        title="Delta-R",
        description="Applies delta-R restriction to combination of two objects.<br/><br/>" \
                    "&Delta;R = &radic;<span style=\"text-decoration:overline;\">&nbsp;&Delta;&eta;&sup2; + &Delta;&phi;&sup2;&nbsp;</span><br/><br/>" \
                    "<strong>Example:</strong> <pre>dist{MU20, MU20}[DR_SAMPLE]</pre>"
    ),
    CutSpecification(
        name=tmGrammar.MASS,
        object=tmGrammar.mass,
        type=tmGrammar.MASS,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU, tmGrammar.ETM, tmGrammar.HTM, tmGrammar.ETMHF],
        functions=[tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_orm, tmGrammar.mass_trv, tmGrammar.mass_trv_orm],
        range_precision=1,
        range_step=0.2,
        range_unit="GeV",
        title="Invariant mass",
        description="Applies invariant mass restriction to combination of two objects.<br/><br/>" \
                    "M = &radic;<span style=\"text-decoration:overline;\">&nbsp;2 <em>pt1</em> <em>pt2</em> (cosh(&Delta;&eta;) - cos(&Delta;&phi;))&nbsp;</span><br/><br/>" \
                    "<strong>Example:</strong> <pre>mass{MU20, MU20}[MASS_Z]</pre>"
    ),
    CutSpecification(
        name=tmGrammar.TBPT,
        object=tmGrammar.mass,
        type=tmGrammar.TBPT,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU, tmGrammar.ETM, tmGrammar.HTM, tmGrammar.ETMHF],
        functions=[tmGrammar.comb, tmGrammar.comb_orm, tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass_inv, tmGrammar.mass_inv_orm, tmGrammar.mass_trv, tmGrammar.mass_trv_orm],
        range_precision=1,
        range_step=0.1,
        range_unit="GeV",
        title="Two body Pt",
        description="Applies two body Pt (energy of origin object) threshold to combination of two objects.<br/><br/>"
                    "<strong>Example:</strong> <pre>mass_inv{MU20, MU20}[MASS_Z, TBPT_A]</pre>"
    ),
    CutSpecification(
        name=tmGrammar.ORMDETA,
        object=tmGrammar.dist,
        type=tmGrammar.ORMDETA,
        objects=[tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm, tmGrammar.mass_trv_orm],
        range_precision=3,
        range_step=0.001,
        title="Delta eta",
        description="Applies delta eta overlap removal restriction to combination of two/three objects.<br/><br/>" \
                    "<strong>Example:</strong> <pre>comb_orm{TAU0, TAU0, JET0}[ORMDETA_SAMPLE]</pre>"
    ),
    CutSpecification(
        name=tmGrammar.ORMDPHI,
        object=tmGrammar.dist,
        type=tmGrammar.ORMDPHI,
        objects=[tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm, tmGrammar.mass_trv_orm],
        range_precision=3,
        range_step=0.001,
        range_unit="rad",
        title="Delta phi",
        description="Applies delta phi overlap removal restriction to combination of two/three objects.<br/><br/>" \
                    "<strong>Example:</strong> <pre>comb_orm{TAU0, TAU0, JET0}[ORMDPHI_SAMPLE]</pre>"
    ),
    CutSpecification(
        name=tmGrammar.ORMDR,
        object=tmGrammar.dist,
        type=tmGrammar.ORMDR,
        objects=[tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm, tmGrammar.mass_trv_orm],
        range_precision=1,
        range_step=0.1,
        title="Delta-R Overlap Removal",
        description="Applies delta-R overlap removal restriction to combination of two/three objects.<br/><br/>" \
                    "&Delta;R = &radic;<span style=\"text-decoration:overline;\">&nbsp;&Delta;&eta;&sup2; + &Delta;&phi;&sup2;&nbsp;</span><br/><br/>" \
                    "<strong>Example:</strong> <pre>comb_orm{TAU0, TAU0, JET0}[ORMDR_SAMPLE]</pre>"
    ),
)
