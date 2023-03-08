import logging

import tmGrammar
import tmTable

from tmGrammar import isGate as isOperator
from tmGrammar import isObject, isFunction
from tmEditor.core import XmlDecoder, XmlEncoder
from tmEditor.core.Menu import Menu
from tmEditor.core.Algorithm import Object, External, Cut, Algorithm
from tmEditor.core.Algorithm import toObject, toExternal
from tmEditor.core.Algorithm import functionObjects, functionCuts, functionObjectsCuts
from tmEditor.core.Algorithm import objectCuts

UTM_VERSION: str = "0.11.0"


class TestMenu:

    def test_isOperator(self):
        for op in tmGrammar.gateName:
            assert isOperator(op) is True
        for op in ("comb", "MU10", "MU-ISO_Q"):
            assert isOperator(op) is False

    def test_isObject(self):
        assert isObject("MU10") is True
        assert isObject("EG100-1") is True
        assert isObject("TAU.eq.50p5+1") is True
        assert isObject("comb") is False
        assert isObject("AND") is False
        assert isObject("NOT") is False

    def test_isFunction(self):
        assert isFunction("comb{MU20,MU10}") is True
        assert isFunction("dist{MU100,JET100}[DPHI_Q]") is True
        assert isFunction("dist{MU20[MU-PHI_Q],MU10[MU-PHI_Q]}[DPHI_Q]") is True
        assert isFunction("MU-ISO_Q") is False
        assert isFunction("AND") is False
        assert isFunction("MU10") is False

    def test_toObject(self):
        cases = {
            "MU10": dict(name="MU10", threshold="10", type=tmGrammar.MU, comparison_operator=tmGrammar.GE, bx_offset=0),
            "EG.ge.60+1": dict(name="EG60+1", threshold="60", type=tmGrammar.EG, comparison_operator=tmGrammar.GE, bx_offset=1),
            "TAU.eq.260p5-2": dict(name="TAU.eq.260p5-2", threshold="260p5", type=tmGrammar.TAU, comparison_operator=tmGrammar.EQ, bx_offset=-2),
            "JET4[JET-DISP_LLP]": dict(name="JET4", threshold="4", type=tmGrammar.JET, comparison_operator=tmGrammar.GE, bx_offset=0),
        }
        for token, ref in cases.items():
            assert toObject(token) == Object(**ref), "missmatch at object requirment conversion"

    def test_toExternal(self):
        cases = {
            "BPTX_plus": dict(name="BPTX_plus", bx_offset=0),
            "BPTX_minus+1": dict(name="BPTX_minus+1", bx_offset=+1,),
            "BPTX_minus-1": dict(name="BPTX_minus-1", bx_offset=-1),
            "BPTX_plus_AND_minus+2": dict(name="BPTX_plus_AND_minus+2", bx_offset=+2),
        }
        for token, ref in cases.items():
            assert toExternal(token) == External(**ref)

    def test_functionObjects(self):
        def to_objects(*args): return [toObject(token) for token in args]
        cases = {
            "dist{MU10,MU20}[DR_Q]": to_objects("MU10", "MU20"),
            "comb{EG80+1,EG60+1,EG40+1}": to_objects("EG80+1", "EG60+1", "EG40+1"),
            "comb{TAU80[TAU-ISO_Q],TAU60[TAU-ISO_Q],TAU40[TAU-ISO_Q],TAU20[TAU-ISO_Q]}": to_objects("TAU80", "TAU60", "TAU40", "TAU20"),
        }
        for token, ref in cases.items():
            assert functionObjects(token) == ref

    def test_functionCuts(self):
        cases = {
            "comb{MU10,MU20}": [],
            "dist{MU10,MU20}[DR_Q]": ["DR_Q"],
            "dist{EG80+1,EG60+1}[DETA_Q,DPHI_Q]": ["DETA_Q", "DPHI_Q"],
            "dist{TAU80[TAU-ISO_Q],TAU20[TAU-ISO_Q]}[DETA_Q]": ["DETA_Q"],
            "mass_inv{MU10,MU20}[MASS_X,CHGCOR_OS]": ["MASS_X", "CHGCOR_OS"],
            "mass_inv_3{MU10,MU20,MU20}[MASS_X]": ["MASS_X"],
        }
        for token, ref in cases.items():
            assert functionCuts(token) == ref

    def test_functionObjectsCuts(self):
        cases = {
            "comb{MU20,MU10}": [[], []],
            "comb{MU20[MU-ISO_Q],MU10[MU-ISO_Q]}": [["MU-ISO_Q"], ["MU-ISO_Q"]],
            "comb{TAU20[TAU-ETA_Q,TAU-PHI_Q],TAU20[TAU-ETA_Q,TAU-PHI_Q]}": [["TAU-ETA_Q", "TAU-PHI_Q"], ["TAU-ETA_Q", "TAU-PHI_Q"]],
            "comb{TAU20[TAU-PHI_Q],TAU20[TAU-ETA_Q]}": [["TAU-PHI_Q"], ["TAU-ETA_Q"]],
            "comb{MU80,MU60,MU40,MU20}": [[], [], [], []],
            "comb{MU80[MU-ETA_A],MU60[MU-ETA_B],MU40[MU-ETA_C],MU20[MU-ETA_D]}": [["MU-ETA_A"], ["MU-ETA_B"], ["MU-ETA_C"], ["MU-ETA_D"]],
            "comb{MU400[MU-ETA_Q],MU300[MU-ETA_Q,MU-PHI_Q,MU-ISO_Q],MU200[MU-PHI_Q],MU100[MU-ETA_Q]}": [["MU-ETA_Q"], ["MU-ETA_Q","MU-PHI_Q","MU-ISO_Q"], ["MU-PHI_Q"], ["MU-ETA_Q"]],
        }
        for token, ref in cases.items():
            assert functionObjectsCuts(token) == ref

    def test_objectCuts(self):
        cases = {
            "MU10": [],
            "MU80[MU-ISO_Q,MU-QLTY_Q]": ["MU-ISO_Q", "MU-QLTY_Q"],
            "TAU10[TAU-ETA_Q,TAU-PHI_Q]": ["TAU-ETA_Q", "TAU-PHI_Q"],
            "JET0[JET-DISP_LLP]": ["JET-DISP_LLP"],
        }
        for token, ref in cases.items():
            assert objectCuts(token) == ref

    def test_serdes(self):
        menu = Menu()
        menu.menu.name = "L1Menu_Unittest"
        # menu.scale = tmTable.Scale()
        # menu.scale.scales = tmTable.Table()
        # menu.extSignals = tmTable.ExtSignal()
        menu.addObject(Object("MU10", "MU", 10))
        menu.addObject(Object("MU20", "MU", 20))
        menu.addCut(Cut("MU-ETA_2p1", "MU", "ETA", -2.1, +2.1))
        menu.addAlgorithm(Algorithm(42, "L1_DoubleMu_er2p1", "comb{MU20[MU-ETA_2p1],MU10[MU-ETA_2p1]}"))
        # file, filename = tempfile.mkstemp()
        # open(filename).close()
        # XmlEncoder.dump(menu, filename)
        # menu = XmlDecoder.load(filename)
        logging.info("algorithms: %s", menu.algorithms)
        logging.info("cuts: %s", menu.cuts)
        logging.info("objects: %s", menu.objects)

    def test_version(self):
        assert tmGrammar.__version__ == UTM_VERSION
        assert tmTable.__version__ == UTM_VERSION
