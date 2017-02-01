# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

import tmGrammar

tmGrammar.ET = "ET"

kET = 'ET'
kCOUNT = 'COUNT'

ThresholdObjectTypes = (
    # Muon objects
    tmGrammar.MU,
    # Calorimeter objects
    tmGrammar.EG,
    tmGrammar.JET,
    tmGrammar.TAU,
    # Energy sums
    tmGrammar.ETM,
    tmGrammar.HTM,
    tmGrammar.ETT,
    tmGrammar.HTT,
    tmGrammar.ETTEM,
    tmGrammar.ETMHF,
)
"""Ordered list of ET threshold type object names."""

CountObjectTypes = (
    # Minimum Bias
    tmGrammar.MBT0HFP,
    tmGrammar.MBT1HFP,
    tmGrammar.MBT0HFM,
    tmGrammar.MBT1HFM,
    # Tower counts
    tmGrammar.TOWERCOUNT,
)
"""Ordered list of count type object names."""

ObjectTypes = ThresholdObjectTypes + CountObjectTypes
"""Ordered list of all supported threshold and count object types."""

ExternalObjectTypes = (
    tmGrammar.EXT,
)
"""Ordered list of supported external signal types."""

CutTypes = (
    tmGrammar.ETA,
    tmGrammar.PHI,
    tmGrammar.QLTY,
    tmGrammar.ISO,
    tmGrammar.CHG,
    tmGrammar.CHGCOR,
    tmGrammar.DETA,
    tmGrammar.DPHI,
    tmGrammar.DR,
    tmGrammar.MASS,
)
"""Ordered list of supported cut types."""

ThresholdCutNames = (
    "-".join((tmGrammar.MU, tmGrammar.ET)),
    "-".join((tmGrammar.EG, tmGrammar.ET)),
    "-".join((tmGrammar.JET, tmGrammar.ET)),
    "-".join((tmGrammar.TAU, tmGrammar.ET)),
    "-".join((tmGrammar.ETM, tmGrammar.ET)),
    "-".join((tmGrammar.HTM, tmGrammar.ET)),
    "-".join((tmGrammar.ETT, tmGrammar.ET)),
    "-".join((tmGrammar.HTT, tmGrammar.ET)),
    "-".join((tmGrammar.ETTEM, tmGrammar.ET)),
    "-".join((tmGrammar.ETMHF, tmGrammar.ET)),
)
"""Ordered list of threshold cut names."""

ObjectCutTypes = (
    tmGrammar.ETA,
    tmGrammar.PHI,
    tmGrammar.ISO,
    tmGrammar.QLTY,
    tmGrammar.CHG,
)
"""Orderd list of cut type names."""

ObjectComparisonTypes = (
    tmGrammar.GE,
    tmGrammar.EQ,
)
"""Ordered list of supported object comparison types."""

# -----------------------------------------------------------------------------
#  Mappings
# -----------------------------------------------------------------------------

ObjectScaleMap = {
    tmGrammar.MU: kET,
    tmGrammar.EG: kET,
    tmGrammar.TAU: kET,
    tmGrammar.JET: kET,
    tmGrammar.ETT: kET,
    tmGrammar.HTT: kET,
    tmGrammar.ETM: kET,
    tmGrammar.HTM: kET,
    tmGrammar.ETTEM: kET,
    tmGrammar.ETMHF: kET,
    tmGrammar.MBT0HFP: kCOUNT,
    tmGrammar.MBT1HFP: kCOUNT,
    tmGrammar.MBT0HFM: kCOUNT,
    tmGrammar.MBT1HFM: kCOUNT,
    tmGrammar.TOWERCOUNT: kCOUNT,
}
"""Mapping of threshold/count scale types for objects."""
