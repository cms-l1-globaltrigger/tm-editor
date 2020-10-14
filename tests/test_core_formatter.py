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

import unittest

class CoreFormatterTests(unittest.TestCase):

    def test_fHex(self):
        self.assertEqual(fHex(0.42), '0x0')
        self.assertEqual(fHex(1), '0x1')
        self.assertEqual(fHex(42), '0x2a')

    def test_fCompress(self):
        self.assertEqual(fCompress([0]), '0')
        self.assertEqual(fCompress([0,1]), '0-1')
        self.assertEqual(fCompress([0,2]), '0, 2')
        self.assertEqual(fCompress([0,1,2,3,5,7,8,9]), '0-3, 5, 7-9')

    def test_fFileSize(self):
        self.assertEqual(fFileSize(1234), '1.2KiB')

    def test_fCutValue(self):
        self.assertEqual(fCutValue(0), '+0.000')
        self.assertEqual(fCutValue(42, 1), '+42.0')

    def test_fCutData(self):
        pass

    def test_fCutLabel(self):
        pass

    def test_fCutLabelRichText(self):
        pass

    def test_fThreshold(self):
        self.assertEqual(fThreshold("2p5"), '2.5 GeV')

    def test_fCounts(self):
        self.assertEqual(fCounts("42"), '42 counts')

    def test_fComparison(self):
        self.assertEqual(fComparison(tmGrammar.GE), '>=')
        self.assertEqual(fComparison(tmGrammar.EQ), '==')

    def test_fBxOffset(self):
        self.assertEqual(fBxOffset(2), '+2')
        self.assertEqual(fBxOffset(-2), '-2')

if __name__ == '__main__':
    unittest.main()
