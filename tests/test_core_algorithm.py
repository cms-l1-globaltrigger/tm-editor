import tmGrammar

from tmEditor.core.Algorithm import Algorithm

import unittest

class CoreAlgorithmTests(unittest.TestCase):

    def test_Algorithm(self):
        algorithm = Algorithm(42, 'L1_Mu0', 'MU0')
        self.assertEqual(algorithm.index, 42)
        self.assertEqual(algorithm.name, 'L1_Mu0')
        self.assertEqual(algorithm.expression, 'MU0')
        self.assertEqual(algorithm.comment, '')
        self.assertEqual(algorithm.labels, [])

    def test_Algorithm_tokens(self):
        algorithm = Algorithm(0, 'L1_Mu0', 'MU0')
        self.assertEqual(algorithm.tokens(), ['MU0'])
        algorithm.expression = 'JET1 AND TAU2'
        self.assertEqual(algorithm.tokens(), ['JET1', 'TAU2', 'AND'])
        algorithm.expression = 'JET1 AND (TAU2 OR MU3)'
        self.assertEqual(algorithm.tokens(), ['JET1', 'TAU2', 'MU3', 'OR', 'AND'])

if __name__ == '__main__':
    unittest.main()
