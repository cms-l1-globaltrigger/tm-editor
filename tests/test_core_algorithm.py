import tmGrammar

from tmEditor.core.Algorithm import Algorithm


class TestCoreAlgorithm:

    def test_Algorithm(self):
        algorithm = Algorithm(42, "L1_Mu0", "MU0")
        assert algorithm.index == 42
        assert algorithm.name == "L1_Mu0"
        assert algorithm.expression == "MU0"
        assert algorithm.comment == ""
        assert algorithm.labels == []

    def test_Algorithm_tokens(self):
        algorithm = Algorithm(0, "L1_Mu0", "MU0")
        assert algorithm.tokens() == ["MU0"]
        algorithm.expression = "JET1 AND TAU2"
        assert algorithm.tokens() == ["JET1", "TAU2", "AND"]
        algorithm.expression = "JET1 AND (TAU2 OR MU3)"
        assert algorithm.tokens() == ["JET1", "TAU2", "MU3", "OR", "AND"]
