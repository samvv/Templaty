
from templately.scanner import Scanner
from templately.parser import Parser
from templately.ast import *

import unittest

class TestParser(unittest.TestCase):

    def test_string_lit(self):
        sc = Scanner('#<string_lit>', "'Hello!'", True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, ConstExpression)
        self.assertEqual(e.value, 'Hello!')

    def test_simple_add(self):
        sc = Scanner('#<simple_add>', 'a + b', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertEqual(len(e.operands), 2)
        self.assertIsInstance(e.operands[0], VarRefExpression)
        self.assertEqual(e.operands[0].name, 'a')
        self.assertIsInstance(e.operands[1], VarRefExpression)
        self.assertEqual(e.operands[1].name, 'b')

    def test_nested_add(self):
        sc = Scanner('#<nested_add>', '(a + b) + c', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertEqual(len(e.operands), 2)
        arg1 = e.operands[0]
        self.assertIsInstance(arg1, AppExpression)
        self.assertEqual(arg1.operands[0].name, 'a')
        self.assertEqual(arg1.operands[1].name, 'b')
        arg2 = e.operands[1]
        self.assertIsInstance(arg2, VarRefExpression)
        self.assertEqual(arg2.name, 'c')

    def test_binary_operator_precedence1(self):
        sc = Scanner('#<binary_operator_precedence1>', 'a * b + c', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertEqual(len(e.operands), 2)
        arg1 = e.operands[0]
        self.assertIsInstance(arg1, AppExpression)
        self.assertEqual(arg1.operands[0].name, 'a')
        self.assertEqual(arg1.operands[1].name, 'b')
        arg2 = e.operands[1]
        self.assertIsInstance(arg2, VarRefExpression)
        self.assertEqual(arg2.name, 'c')

    def test_binary_operator_precedence2(self):
        sc = Scanner('#<binary_operator_precedence2>', 'a + b * c', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertEqual(len(e.operands), 2)
        arg1 = e.operands[0]
        self.assertIsInstance(arg1, VarRefExpression)
        self.assertEqual(arg1.name, 'a')
        arg2 = e.operands[1]
        self.assertIsInstance(arg2, AppExpression)
        self.assertEqual(arg2.operands[0].name, 'b')
        self.assertEqual(arg2.operands[1].name, 'c')


    def test_binary_operator_precedence3(self):
        sc = Scanner('#<binary_operator_precedence3>', 'a * b * c', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertEqual(len(e.operands), 2)
        arg1 = e.operands[0]
        self.assertIsInstance(arg1, AppExpression)
        self.assertEqual(arg1.operands[0].name, 'a')
        self.assertEqual(arg1.operands[1].name, 'b')
        arg2 = e.operands[1]
        self.assertIsInstance(arg2, VarRefExpression)
        self.assertEqual(arg2.name, 'c')


    def test_binary_operator_precedence4(self):
        sc = Scanner('#<binary_operator_precedence4>', 'a ** b ** c', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertEqual(len(e.operands), 2)
        arg1 = e.operands[0]
        self.assertIsInstance(arg1, VarRefExpression)
        self.assertEqual(arg1.name, 'a')
        arg2 = e.operands[1]
        self.assertIsInstance(arg2, AppExpression)
        self.assertEqual(arg2.operands[0].name, 'b')
        self.assertEqual(arg2.operands[1].name, 'c')

