"""Settings module."""

from .toolbox import CutSpecificationPool, CutSpecification

import tmGrammar

__all__ = ["MaxAlgorithms", "CutSpecs"]

MaxAlgorithms = 512
"""Maximum number of supported algorithms."""

VersionUrl = "https://svnweb.cern.ch/trac/cactus/export/HEAD/trunk/cactusprojects/ugt/menu/version.json"
"""Server side version and scale set information URL."""

DefaultScaleSetUri = "scales/L1Menu_{scale_set}.xml"
"""Default URI format string for server side scale set XML files."""

DefaultExtSignalSetUri = "cabling/L1Menu_{ext_signal_set}.xml"
"""Default URI format string for server side external signal set XML files."""

DownloadSite = "https://cern.ch/globaltrigger/upgrade/tme/downloads"
"""Web URL providing download information."""

ContentsURL = "https://cern.ch/globaltrigger/upgrade/tme/userguide"
"""Web URL hosting the user guide."""

Empty = ""
"""Empty string entry."""

ModelsURL = "https://globaltrigger.web.cern.ch/upgrade/tme/models"
"""Web URL models description for NN MODELs."""

CutSpecs = CutSpecificationPool(
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.UPT),
        object=tmGrammar.MU,
        type=tmGrammar.UPT,
        range_step=1.0,
        title="Muon unconstrained pt",
        description="Threshold for unconstrained pt."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.ETA),
        object=tmGrammar.MU,
        type=tmGrammar.ETA,
        range_precision=3,
        count_maximum=5,
        title="Muon eta",
        description="Restricts valid eta range for muon object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.PHI),
        object=tmGrammar.MU,
        type=tmGrammar.PHI,
        range_precision=3,
        count_maximum=2,
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
        description="Two bits for isolation, bit 0 represents isolation, meaning of bit 1 is currently not defined.",
        data={
            "0": "non-isolated",
            "1": "isolated",
            "2": "n/a",
            "3": "n/a+isolated"
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
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.IP),
        object=tmGrammar.MU,
        type=tmGrammar.IP,
        title="Muon impact parameter",
        description="Two bits for impact parameter.",
        data={
            "0": "impact parameter 0",
            "1": "impact parameter 1",
            "2": "impact parameter 2",
            "3": "impact parameter 3"
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
        name=CutSpecification.join(tmGrammar.MU, tmGrammar.INDEX),
        object=tmGrammar.MU,
        type=tmGrammar.INDEX,
        range_precision=0,
        count_maximum=5,
        title="Muon index",
        description="Restricts valid index range for muon object requirement."
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.EG, tmGrammar.ETA),
        object=tmGrammar.EG,
        type=tmGrammar.ETA,
        range_precision=3,
        count_maximum=5,
        title="Electron/gamma eta",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.EG, tmGrammar.PHI),
        object=tmGrammar.EG,
        type=tmGrammar.PHI,
        range_precision=3,
        count_maximum=2,
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
        description="Two bits for isolation, bit 0 represents isolation, meaning of bit 1 is currently not defined.",
        data={
            "0": "non-isolated",
            "1": "isolated",
            "2": "n/a",
            "3": "n/a+isolated"
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
        range_precision=3,
        count_maximum=5,
        title="Jet eta",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.JET, tmGrammar.PHI),
        object=tmGrammar.JET,
        type=tmGrammar.PHI,
        range_precision=3,
        count_maximum=2,
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
        name=CutSpecification.join(tmGrammar.JET, tmGrammar.DISP),
        object=tmGrammar.JET,
        type=tmGrammar.DISP,
        title="Jet displaced",
        description="Displaced jet for LLP",
        data_exclusive=True,
        data={
            "0": "non-displaced",
            "1": "displaced"
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
        range_precision=3,
        count_maximum=5,
        title="Tau eta",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.TAU, tmGrammar.PHI),
        object=tmGrammar.TAU,
        type=tmGrammar.PHI,
        range_precision=3,
        count_maximum=2,
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
        description="Two bits for isolation, bit 0 represents isolation, meaning of bit 1 is currently not defined.",
        data={
            "0": "non-isolated",
            "1": "isolated",
            "2": "n/a",
            "3": "n/a+isolated"
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
        range_precision=3,
        count_maximum=2,
        range_unit="rad",
        title="Missing energy phi",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.ETMHF, tmGrammar.PHI),
        object=tmGrammar.ETMHF,
        type=tmGrammar.PHI,
        range_precision=3,
        count_maximum=2,
        range_unit="rad",
        title="Missing energy HF phi",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.HTM, tmGrammar.PHI),
        object=tmGrammar.HTM,
        type=tmGrammar.PHI,
        range_precision=3,
        count_maximum=2,
        range_unit="rad",
        title="Missing Ht phi",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.HTMHF, tmGrammar.PHI),
        object=tmGrammar.HTMHF,
        type=tmGrammar.PHI,
        range_precision=3,
        count_maximum=2,
        range_unit="rad",
        title="Missing Ht HF phi",
        description=""
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.ADT, tmGrammar.ASCORE),
        object=tmGrammar.ADT,
        type=tmGrammar.ASCORE,
        range_precision=0,
        range_step=1,
        count_minimum=1,
        count_maximum=1,
        title="Anomaly score",
        description=(
            "<p>Threshold score for Anomaly Detection Trigger. Maximum value 10^8 (100000000).</p>"
            "<p><strong>Example:</strong> <pre>ADT[ADT-ASCORE_1234]</pre></p>"
        )
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.AXO, tmGrammar.SCORE),
        object=tmGrammar.AXO,
        type=tmGrammar.SCORE,
        range_precision=0,
        range_step=1,
        count_minimum=1,
        count_maximum=1,
        title="AXOL1TL Trigger score",
        description=(
            "<p>Threshold for AXO - AXOL1TL Trigger score (max. 32 bits), because of different models. Maximum value 2^32 (4294967296)</p>"
            "<p>Only valid with an additional MODEL cut.</p>"
            "<p><strong>Example:</strong> <pre>AXO[AXO-SCORE_1234]</pre></p>"
        )
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.AXO, tmGrammar.MODEL),
        object=tmGrammar.AXO,
        type=tmGrammar.MODEL,
        count_minimum=1,
        count_maximum=1,
        title="AXOL1TL Trigger model",
        description=(
            f"<p>Name of AXOL1TL Trigger model, see <a href=\"{ModelsURL}\">available Models</a>.</p>"
            "<p>Only valid with an additional SCORE cut.</p>"
            "<p><strong>Example:</strong> <pre>AXO[AXO-MODEL_v1]</pre></p>"
        )
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.TOPO, tmGrammar.SCORE),
        object=tmGrammar.TOPO,
        type=tmGrammar.SCORE,
        range_precision=0,
        range_step=1,
        count_minimum=1,
        count_maximum=1,
        title="Topological Trigger score",
        description=(
            "<p>Threshold for Topological Trigger score (max. 32 bits), because of different models. Maximum value 2^32 (4294967296).</p>"
            "<p>Only valid with an additional MODEL cut.</p>"
            "<p><strong>Example:</strong> <pre>TOPO[TOPO-SCORE_1234]</pre></p>"
        )
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.TOPO, tmGrammar.MODEL),
        object=tmGrammar.TOPO,
        type=tmGrammar.MODEL,
        count_minimum=1,
        count_maximum=1,
        title="Topological Trigger model",
        description=(
            f"<p>Name of Topological Trigger model, see <a href=\"{ModelsURL}\">available Models</a>.</p>"
            "<p>Only valid with an additional SCORE cut.</p>"
            "<p><strong>Example:</strong> <pre>TOPO[TOPO-MODEL_hh_ele_v1]</pre><p>"
        )
    ),
    CutSpecification(
        name=CutSpecification.join(tmGrammar.CICADA, tmGrammar.CSCORE),
        object=tmGrammar.CICADA,
        type=tmGrammar.CSCORE,
        range_precision=8,
        range_step=1 / (2**8),  # TODO fallback
        count_minimum=1,
        count_maximum=1,
        title="CICADA Trigger Anomaly Detection score",
        description=(
            "<p>Threshold for CICADA Anomaly Detection Trigger score. Step size = 1/2^8 (0.00390625), where 8 is bitwidth of CICADA AD Decimal part.</p>"
            "<p>Maximum value = 256 (2^8, where where 8 is bitwidth of CICADA AD Integer part.</p>"
            "<p><strong>Example:</strong> <pre>CICADA[CICADA-CSCORE_4p273]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.CHGCOR,
        object=Empty,
        type=tmGrammar.CHGCOR,
        objects=[tmGrammar.MU],
        functions=[tmGrammar.comb, tmGrammar.dist, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_upt, tmGrammar.mass_inv_dr, tmGrammar.mass_inv_3],
        title="Charge correlation",
        description=(
            "<p>Applies charge correlation restriction to combinations of two or more muon objects. It can be applied to functions comb, dist, mass_inv and mass_trv.</p>"
            "<p><strong>Example:</strong> <pre>comb{MU20, MU20}[CHGCOR_OS]</pre></p>"
        ),
        data_exclusive=True,
        data={
            "ls": "like sign",
            "os": "opposite sign"
        }
    ),
    CutSpecification(
        name=tmGrammar.DETA,
        object=Empty,
        type=tmGrammar.DETA,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_upt, tmGrammar.mass_inv_orm],
        range_precision=3,
        range_step=0.001,
        title="Delta eta",
        description=(
            "<p>Applies delta eta restriction to combination of two objects.</p>"
            "<p><strong>Example:</strong> <pre>dist{MU20, MU20}[DETA_SAMPLE]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.DPHI,
        object=Empty,
        type=tmGrammar.DPHI,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_upt, tmGrammar.mass_inv_orm, tmGrammar.mass_trv],
        range_precision=3,
        range_step=0.001,
        range_unit="rad",
        title="Delta phi",
        description=(
            "<p>Applies delta phi restriction to combination of two objects.</p>"
            "<p><strong>Example:</strong> <pre>dist{MU20, MU20}[DPHI_SAMPLE]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.DR,
        object=Empty,
        type=tmGrammar.DR,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_upt, tmGrammar.mass_inv_orm],
        range_precision=1,
        range_step=0.1,
        title="Delta-R",
        description=(
            "<p>Applies delta-R restriction to combination of two objects.</p>"
            "<p>&Delta;R = &radic;<span style=\"text-decoration:overline;\">&nbsp;&Delta;&eta;&sup2; + &Delta;&phi;&sup2;&nbsp;</span></p>"
            "<p><strong>Example:</strong> <pre>dist{MU20, MU20}[DR_SAMPLE]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.MASS,
        object=Empty,
        type=tmGrammar.MASS,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU, tmGrammar.ETM, tmGrammar.HTM, tmGrammar.ETMHF, tmGrammar.HTMHF],
        functions=[tmGrammar.mass, tmGrammar.mass_inv, tmGrammar.mass_inv_3, tmGrammar.mass_inv_orm, tmGrammar.mass_trv],
        range_precision=1,
        range_step=0.2,
        range_unit="GeV",
        title="Invariant or Transverse mass",
        description=(
            "<p>Applies invariant or transverse mass restriction to combination of two (or three) objects depending on the applied function.</p>"
            "<p>Calculation of invariant mass:</p>"
            "<p>M<sub>0</sub> = &radic;<span style=\"text-decoration:overline;\">&nbsp;2 <em>pt1</em> <em>pt2</em> (cosh(&Delta;&eta;) - cos(&Delta;&phi;))&nbsp;</span></p>"
            "<p>Calculation of transverse mass:</p>"
            "<p>M<sub>T</sub> = &radic;<span style=\"text-decoration:overline;\">&nbsp;2 <em>pt1</em> <em>pt2</em> (1 - cos(&Delta;&phi;))&nbsp;</span></p>"
            "<p><strong>Example:</strong> <pre>mass_inv{MU20, MU20}[MASS_Z]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.MASSUPT,
        object=Empty,
        type=tmGrammar.MASSUPT,
        objects=[tmGrammar.MU],
        functions=[tmGrammar.mass_inv_upt],
        range_precision=1,
        range_step=0.2,
        range_unit="GeV",
        title="Invariant mass for muon unconstrained pt",
        description=(
            "<p>Applies invariant mass restriction to combination of two objects.</p>"
            "<p>Calculation of invariant mass:</p>"
            "<p>M<sub>0</sub> = &radic;<span style=\"text-decoration:overline;\">&nbsp;2 <em>upt1</em> <em>upt2</em> (cosh(&Delta;&eta;) - cos(&Delta;&phi;))&nbsp;</span></p>"
            "<p><strong>Example:</strong> <pre>mass_inv_upt{MU20, MU20}[MASSUPT_Z]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.MASSDR,
        object=Empty,
        type=tmGrammar.MASSDR,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.mass_inv_dr],
        range_precision=1,
        range_step=0.2,
        range_unit="GeV",
        title="Invariant mass divided by delta-R",
        description=(
            "<p>Applies invariant mass divided by delta-R restriction of two objects.</p>"
            "<p>Calculation of invariant mass/delta-R:</p>"
            "<p>M<sub>0</sub>/&Delta;R = &radic;<span style=\"text-decoration:overline;\">&nbsp;2 <em>pt1</em> <em>pt2</em> (cosh(&Delta;&eta;) - cos(&Delta;&phi;))</span>/&Delta;R</p>"
            "<p><strong>Example:</strong> <pre>mass_inv_dr{MU20, MU20}[MASSDR_X]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.TBPT,
        object=Empty,
        type=tmGrammar.TBPT,
        objects=[tmGrammar.MU, tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU, tmGrammar.ETM, tmGrammar.HTM, tmGrammar.ETMHF, tmGrammar.HTMHF],
        functions=[tmGrammar.comb, tmGrammar.comb_orm, tmGrammar.dist, tmGrammar.dist_orm, tmGrammar.mass_inv, tmGrammar.mass_inv_upt, tmGrammar.mass_inv_orm, tmGrammar.mass_trv],
        range_precision=1,
        range_step=0.1,
        range_unit="GeV",
        title="Two body Pt",
        description=(
            "<p>Applies two body Pt (energy of origin object) threshold to combination of two objects.</p>"
            "<p><strong>Example:</strong> <pre>mass_inv{MU20, MU20}[MASS_Z, TBPT_A]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.ORMDETA,
        object=Empty,
        type=tmGrammar.ORMDETA,
        objects=[tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm],
        range_precision=3,
        range_step=0.001,
        title="Delta eta",
        description=(
            "<p>Applies delta eta overlap removal restriction to combination of two/three objects.</p>"
            "<p><strong>Example:</strong> <pre>comb_orm{TAU0, TAU0, JET0}[ORMDETA_SAMPLE]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.ORMDPHI,
        object=Empty,
        type=tmGrammar.ORMDPHI,
        objects=[tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm],
        range_precision=3,
        range_step=0.001,
        range_unit="rad",
        title="Delta phi",
        description=(
            "<p>Applies delta phi overlap removal restriction to combination of two/three objects.</p>"
            "<p><strong>Example:</strong> <pre>comb_orm{TAU0, TAU0, JET0}[ORMDPHI_SAMPLE]</pre></p>"
        )
    ),
    CutSpecification(
        name=tmGrammar.ORMDR,
        object=Empty,
        type=tmGrammar.ORMDR,
        objects=[tmGrammar.EG, tmGrammar.JET, tmGrammar.TAU],
        functions=[tmGrammar.comb_orm, tmGrammar.dist_orm, tmGrammar.mass_inv_orm],
        range_precision=1,
        range_step=0.1,
        title="Delta-R Overlap Removal",
        description=(
            "<p>Applies delta-R overlap removal restriction to combination of two/three objects.</p>"
            "<p>&Delta;R = &radic;<span style=\"text-decoration:overline;\">&nbsp;&Delta;&eta;&sup2; + &Delta;&phi;&sup2;&nbsp;</span></p>"
            "<p><strong>Example:</strong> <pre>comb_orm{TAU0, TAU0, JET0}[ORMDR_SAMPLE]</pre></p>"
        )
    ),
)
