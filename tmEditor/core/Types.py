# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

import tmGrammar

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
"""Ordered list of COUNT type object names."""

ExternalObjectTypes = (
    tmGrammar.EXT,
)

ObjectTypes = ThresholdObjectTypes + CountObjectTypes + ExternalObjectTypes
"""List of supported object types (ordered)."""

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
"""List of supported cut types (ordered)."""

ObjectCutTypes = (
    tmGrammar.ETA,
    tmGrammar.PHI,
    tmGrammar.ISO,
    tmGrammar.QLTY,
    tmGrammar.CHG,
)
"""Orderd list of cut type names."""

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
