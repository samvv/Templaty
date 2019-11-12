
import unittest

from templaty.scanner import *

class TestScanner(unittest.TestCase):

    def test_expression_followed_by_text(self):
        tokens = Scanner("#<expr_followed_by_text>", "The {{foo}} is cool!").scan()
        t0 = next(tokens)
        self.assertEqual(t0.type, TEXT)
        t0 = next(tokens)
        self.assertEqual(t0.type, OPEN_EXPRESSION_BLOCK)
        t1 = next(tokens)
        self.assertEqual(t1.type, IDENTIFIER)
        t2 = next(tokens)
        self.assertEqual(t2.type, CLOSE_EXPRESSION_BLOCK)
        t3 = next(tokens)
        self.assertEqual(t3.type, TEXT)
        self.assertEqual(t3.value, ' is cool!')

