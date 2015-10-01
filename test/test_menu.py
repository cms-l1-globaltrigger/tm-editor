#
# Unittests for tmEditor.Menu module
# Author: Bernhard Arnold <bernhard.arnold@cern.ch>
#

import unittest

import tmGrammar
from tmEditor.Menu import (
    Object,
    External,
    isObject,
    toObject,
    toExternal,
    functionObjects,
    functionObjectsCuts,
    objectCuts,
)

class MenuTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_isObject(self):
        self.assertTrue(isObject("MU10"))
        self.assertTrue(isObject("EG100-1"))
        self.assertTrue(isObject("TAU.eq.50p5+1"))
        self.assertFalse(isObject("comb"))
        self.assertFalse(isObject("AND"))
        self.assertFalse(isObject("dist"))

    def test_toObject(self):
        cases = {
            "MU10": dict(name="MU10", threshold="10", type=tmGrammar.MU, comparison_operator=tmGrammar.GE, bx_offset="+0", comment=""),
            "EG.ge.60p0+1": dict(name="EG60p0+1", threshold="60p0", type=tmGrammar.EG, comparison_operator=tmGrammar.GE, bx_offset="+1", comment=""),
            "TAU.eq.260p5-2": dict(name="TAU.eq.260p5-2", threshold="260p5", type=tmGrammar.TAU, comparison_operator=tmGrammar.EQ, bx_offset="-2", comment=""),
        }
        for token, ref in cases.items():
            self.assertEqual(toObject(token), Object(**ref), "missmatch at object requirment conversion")

    def test_toExternal(self):
        cases = {
            "BPTX_plus": dict(name="BPTX_plus", bx_offset="+0", comment=""),
            "BPTX_minus+1": dict(name="BPTX_minus+1", bx_offset="+1", comment=""),
            "BPTX_minus-1": dict(name="BPTX_minus-1", bx_offset="-1", comment=""),
            "BPTX_plus_AND_minus+2": dict(name="BPTX_plus_AND_minus+2", bx_offset="+2", comment=""),
        }
        for token, ref in cases.items():
            self.assertEqual(toExternal(token), External(**ref))

    def test_functionObjects(self):
        def to_objects(*args): return [toObject(token) for token in args]
        cases = {
            "dist{MU10,MU20}[DR_Q]": to_objects("MU10", "MU20"),
            "comb{EG80+1,EG60+1,EG40+1}": to_objects("EG80+1", "EG60+1", "EG40+1"),
            "comb{TAU80[TAU-ISO_Q],TAU60[TAU-ISO_Q],TAU40[TAU-ISO_Q],TAU20[TAU-ISO_Q]}": to_objects("TAU80", "TAU60", "TAU40", "TAU20"),
        }
        for token, ref in cases.items():
            self.assertEqual(functionObjects(token), ref)

    def test_functionObjectsCuts(self):
        cases = {
            "comb{MU20,MU10}": [],
            "comb{MU20[MU-ISO_Q],MU10[MU-ISO_Q]}": ["MU-ISO_Q"],
            "comb{TAU20[TAU-ETA_Q,TAU-PHI_Q],TAU20[TAU-ETA_Q,TAU-PHI_Q]}": ["TAU-ETA_Q", "TAU-PHI_Q"],
            "comb{TAU20[TAU-PHI_Q],TAU20[TAU-ETA_Q]}": ["TAU-ETA_Q", "TAU-PHI_Q"],
            "comb{MU80,MU60,MU40,MU20}": [],
            "comb{MU80[MU-ETA_Q],MU60[MU-ETA_Q],MU40[MU-ETA_Q],MU20[MU-ETA_Q]}": ["MU-ETA_Q"],
            "comb{MU400[MU-ETA_Q],MU300[MU-ETA_Q,MU-PHI_Q,MU-ISO_Q],MU200[MU-PHI_Q],MU100[MU-ETA_Q]}": ["MU-PHI_Q", "MU-ETA_Q", "MU-ISO_Q"],
        }
        for token, ref in cases.items():
            self.assertEqual(functionObjectsCuts(token), ref)

    def test_objectCuts(self):
        cases = {
            "MU10": [],
            "MU80[MU-ISO_Q,MU-QLTY_Q]": ["MU-ISO_Q", "MU-QLTY_Q"],
            "TAU10[TAU-ETA_Q,TAU-PHI_Q]": ["TAU-ETA_Q", "TAU-PHI_Q"],
        }
        for token, ref in cases.items():
            self.assertEqual(objectCuts(token), ref)

if __name__ == '__main__':
    unittest.main()
