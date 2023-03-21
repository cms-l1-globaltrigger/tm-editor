from tmEditor.core.AlgorithmHelper import join
from tmEditor.core.AlgorithmHelper import encode_comparison_operator
from tmEditor.core.AlgorithmHelper import encode_threshold
from tmEditor.core.AlgorithmHelper import decode_threshold
from tmEditor.core.AlgorithmHelper import encode_bx_offset
from tmEditor.core.AlgorithmHelper import encode_cuts


class TestCoreAlgorithmHelper:

    def test_join(self):
        assert join(["foo", "bar", 42], "-") == "foo-bar-42"

    def test_encode_comparison_operator(self):
        assert encode_comparison_operator(".ge.") == ""
        assert encode_comparison_operator(".eq.") == ".eq."

    def test_encode_threshold(self):
        assert encode_threshold(42) == "42"
        assert encode_threshold(42.0) == "42"
        assert encode_threshold(4.2) == "4p2"

    def test_decode_threshold(self):
        assert decode_threshold("42") == 42.0
        assert decode_threshold("42p0") == 42.0
        assert decode_threshold("4p2") == 4.2

    def test_encode_bx_offset(self):
        assert encode_bx_offset(0) == ""
        assert encode_bx_offset(+2) == "+2"
        assert encode_bx_offset(-2) == "-2"

    def test_encode_cuts(self):
        assert encode_cuts([]) == ""
        assert encode_cuts(["MU-ISO_X"]) == "[MU-ISO_X]"
        assert encode_cuts(["MU-ISO_X", "MU-ETA_A", "MU-ETA_B"]) == "[MU-ISO_X,MU-ETA_A,MU-ETA_B]"
