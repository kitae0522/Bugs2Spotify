import unittest
from core.module import Utils


def function(x: int, y: int) -> int:
    return x + y


class FunctionTest(unittest.TestCase):
    def test_function(self):
        result = function(1, 2)
        self.assertEqual(result, 3)


unittest.main()
