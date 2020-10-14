from tmEditor.core.AlgorithmHelper import join
from tmEditor.core.AlgorithmHelper import encode_comparison_operator
from tmEditor.core.AlgorithmHelper import encode_threshold
from tmEditor.core.AlgorithmHelper import decode_threshold
from tmEditor.core.AlgorithmHelper import encode_bx_offset
from tmEditor.core.AlgorithmHelper import encode_cuts

import unittest

class CoreAlgorithmHelperTests(unittest.TestCase):

    def test_join(self):
        self.assertEqual(join(["foo", "bar", 42], "-"), 'foo-bar-42')

    def test_encode_comparison_operator(self):
        self.assertEqual(encode_comparison_operator(".ge."), '')
        self.assertEqual(encode_comparison_operator(".eq."), '.eq.')

    def test_encode_threshold(self):
        self.assertEqual(encode_threshold(42), '42')
        self.assertEqual(encode_threshold(42.0), '42')
        self.assertEqual(encode_threshold(4.2), '4p2')

    def test_decode_threshold(self):
        self.assertEqual(decode_threshold('42'), 42.0)
        self.assertEqual(decode_threshold('42p0'), 42.0)
        self.assertEqual(decode_threshold('4p2'), 4.2)

    def test_encode_bx_offset(self):
        self.assertEqual(encode_bx_offset(0), '')
        self.assertEqual(encode_bx_offset(+2), '+2')
        self.assertEqual(encode_bx_offset(-2), '-2')

    def test_encode_cuts(self):
        self.assertEqual(encode_cuts([]), '')
        self.assertEqual(encode_cuts(['MU-ISO_X']), '[MU-ISO_X]')
        self.assertEqual(encode_cuts(['MU-ISO_X', 'MU-ETA_A', 'MU-ETA_B']), '[MU-ISO_X,MU-ETA_A,MU-ETA_B]')

if __name__ == '__main__':
    unittest.main()
