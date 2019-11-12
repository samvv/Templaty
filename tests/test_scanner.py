
import unittest

from templaty.scanner import *

class TestScanner(unittest.TestCase):

    def test_expression_followed_by_text(self):
        sc = Scanner("#<expr_followed_by_text>", "The {{foo}} is cool!")
        t0 = sc.scan()
        self.assertEqual(t0.type, TEXT)
        t0 = sc.scan()
        self.assertEqual(t0.type, OPEN_EXPRESSION_BLOCK)
        t1 = sc.scan()
        self.assertEqual(t1.type, IDENTIFIER)
        t2 = sc.scan()
        self.assertEqual(t2.type, CLOSE_EXPRESSION_BLOCK)
        t3 = sc.scan()
        self.assertEqual(t3.type, TEXT)
        self.assertEqual(t3.value, ' is cool!')

