import tmGrammar

from tmEditor.core.formatter import fHex
from tmEditor.core.formatter import fCompress
from tmEditor.core.formatter import fFileSize
from tmEditor.core.formatter import fCutValue
from tmEditor.core.formatter import fCutData
from tmEditor.core.formatter import fCutLabel
from tmEditor.core.formatter import fCutLabelRichText
from tmEditor.core.formatter import fThreshold
from tmEditor.core.formatter import fCounts
from tmEditor.core.formatter import fComparison
from tmEditor.core.formatter import fBxOffset


class TestCoreFormatter:

    def test_fHex(self):
        assert fHex(0.42) == "0x0"
        assert fHex(1) == "0x1"
        assert fHex(42) == "0x2a"

    def test_fCompress(self):
        assert fCompress([0]) == "0"
        assert fCompress([0,1]) == "0-1"
        assert fCompress([0,2]) == "0, 2"
        assert fCompress([0,1,2,3,5,7,8,9]) == "0-3, 5, 7-9"

    def test_fFileSize(self):
        assert fFileSize(1234) == "1.2KiB"

    def test_fCutValue(self):
        assert fCutValue(0) == "+0.000"
        assert fCutValue(42, 1) == "+42.0"

    def test_fCutData(self):
        ...

    def test_fCutLabel(self):
        ...

    def test_fCutLabelRichText(self):
        ...

    def test_fThreshold(self):
        assert fThreshold("2p5") == "2.5 GeV"

    def test_fCounts(self):
        assert fCounts("42") == "42 counts"

    def test_fComparison(self):
        assert fComparison(tmGrammar.GE) == ">="
        assert fComparison(tmGrammar.EQ) == "=="

    def test_fBxOffset(self):
        assert fBxOffset(2) == "+2"
        assert fBxOffset(-2) == "-2"
