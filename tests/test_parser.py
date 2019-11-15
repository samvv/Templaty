
from templaty.scanner import Scanner
from templaty.parser import Parser, ParseError, ParseError, ParseError, ParseError
from templaty.ast import *

import unittest

class TestParser(unittest.TestCase):

    def test_empty_code_block(self):
        sc = Scanner('#<empty_code_block>', "{! !}")
        p = Parser(sc)
        s = p.parse()
        self.assertIsInstance(s, CodeBlock)
        self.assertEqual(len(s.module.body), 0)

    def test_expr_code_block(self):
        sc = Scanner('#<empty_code_block>', "{! foo() !}")
        p = Parser(sc)
        s = p.parse()
        self.assertIsInstance(s, CodeBlock)
        self.assertEqual(len(s.module.body), 1)

    def test_text_after_expr(self):
        sc = Scanner('#<text_after_expr>', 'The {{foo}} is cool!')
        p = Parser(sc)
        ast = list(p.parse_all())
        self.assertEqual(ast[2].text, ' is cool!')

    def test_func_app_no_args(self):
        sc = Scanner('#<func_app_no_args>', "foo()", True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertIsInstance(e.operator, VarRefExpression)
        self.assertEqual(e.operator.name, 'foo')
        self.assertEqual(len(e.operands), 0)

    def test_func_app_one_arg(self):
        sc = Scanner('#<func_app_one_arg>', "foo(bar)", True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertIsInstance(e.operator, VarRefExpression)
        self.assertEqual(e.operator.name, 'foo')
        self.assertEqual(len(e.operands), 1)
        self.assertIsInstance(e.operands[0], VarRefExpression)
        self.assertEqual(e.operands[0].name, 'bar')

    def test_func_app_many_args(self):
        sc = Scanner('#<func_app_many_args>', "foo(bar, 1, 2, 3)", True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, AppExpression)
        self.assertIsInstance(e.operator, VarRefExpression)
        self.assertEqual(e.operator.name, 'foo')
        self.assertEqual(len(e.operands), 4)
        self.assertIsInstance(e.operands[0], VarRefExpression)
        self.assertEqual(e.operands[0].name, 'bar')
        self.assertIsInstance(e.operands[1], ConstExpression)
        self.assertEqual(e.operands[1].value, 1)
        self.assertIsInstance(e.operands[2], ConstExpression)
        self.assertEqual(e.operands[2].value, 2)
        self.assertIsInstance(e.operands[3], ConstExpression)
        self.assertEqual(e.operands[3].value, 3)

    def test_for_in_statement(self):
        sc = Scanner('#<for_in_statement>', "{% for i in range(1, 10) %}Foo!{% endfor %}")
        p = Parser(sc)
        s = p.parse_statement()
        self.assertIsInstance(s, ForInStatement)
        self.assertIsInstance(s.pattern, VarPattern)
        self.assertEqual(s.pattern.name, 'i')
        self.assertIsInstance(s.expression, AppExpression)
        self.assertIsInstance(s.expression.operator, VarRefExpression)
        self.assertEqual(s.expression.operator.name, 'range')
        self.assertEqual(len(s.expression.operands), 2)
        self.assertIsInstance(s.expression.operands[0], ConstExpression)
        self.assertEqual(s.expression.operands[0].value, 1)
        self.assertIsInstance(s.expression.operands[1], ConstExpression)
        self.assertEqual(s.expression.operands[1].value, 10)
        self.assertEqual(len(s.body), 1)
        self.assertIsInstance(s.body[0], TextStatement)
        self.assertEqual(s.body[0].text, 'Foo!')

    def test_single_if_statement(self):
        sc = Scanner('#<if_statement>', "{% if somevar %}Foo!{% endif %}")
        p = Parser(sc)
        s = p.parse_statement()
        self.assertIsInstance(s, IfStatement)
        self.assertEqual(len(s.cases), 1)
        cond, cons = s.cases[0]
        self.assertIsInstance(cond, VarRefExpression)
        self.assertEqual(cond.name, 'somevar')
        self.assertEqual(len(cons), 1)
        self.assertIsInstance(cons[0], TextStatement)
        self.assertEqual(cons[0].text, 'Foo!')
        self.assertIsNone(s.alternative)

    def test_fail_parse_close_delimiter(self):
        sc1 = Scanner('#<wrong_for_endif>', "{% for i in range(1, 10) %}Foo!{% endif %}")
        p1 = Parser(sc1)
        self.assertRaises(ParseError, lambda: p1.parse_statement())
        sc2 = Scanner('#<wrong_for_for>', "{% for i in range(1, 20) %}Foo!{% for %}")
        p2 = Parser(sc2)
        self.assertRaises(ParseError, lambda: p2.parse_statement())
        sc3 = Scanner('#<wrong_if_endfor>', "{% if somevmar %}Foo!{% endfor %}")
        p3 = Parser(sc3)
        self.assertRaises(ParseError, lambda: p3.parse_statement())

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

    def test_simple_member_access(self):
        sc = Scanner('#<member_access>', 'foo.bar', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, MemberExpression)
        self.assertIsInstance(e.expression, VarRefExpression)
        self.assertEqual(e.expression.name, 'foo')
        self.assertEqual(len(e.path), 1)
        self.assertEqual(e.path[0], 'bar')

    def test_complex_expression(self):
        sc = Scanner('#<member_access>', '(1 + 2).bar.baz.bax', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, MemberExpression)
        self.assertIsInstance(e.expression, AppExpression)
        self.assertIsInstance(e.expression.operator, VarRefExpression)
        self.assertEqual(e.expression.operator.name, '+')
        self.assertEqual(len(e.expression.operands), 2)
        self.assertIsInstance(e.expression.operands[0], ConstExpression)
        self.assertEqual(e.expression.operands[0].value, 1)
        self.assertIsInstance(e.expression.operands[1], ConstExpression)
        self.assertEqual(e.expression.operands[1].value, 2)
        self.assertEqual(len(e.path), 3)
        self.assertEqual(e.path[0], 'bar')
        self.assertEqual(e.path[1], 'baz')
        self.assertEqual(e.path[2], 'bax')

    def test_simple_index(self):
        sc = Scanner("#<simple_index>", 'foo[2]', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, SliceExpression)
        self.assertIsInstance(e.expression, VarRefExpression)
        self.assertEqual(e.expression.name, 'foo')
        self.assertIsInstance(e.min, ConstExpression)
        self.assertEqual(e.min.value, 2)
        self.assertEqual(e.max, None)

    def test_simple_slice(self):
        sc = Scanner("#<simple_slice>", 'foo[1:2]', True)
        p = Parser(sc)
        e = p.parse_expression()
        self.assertIsInstance(e, SliceExpression)
        self.assertIsInstance(e.expression, VarRefExpression)
        self.assertEqual(e.expression.name, 'foo')
        self.assertIsInstance(e.min, ConstExpression)
        self.assertEqual(e.min.value, 1)
        self.assertIsInstance(e.max, ConstExpression)
        self.assertEqual(e.max.value, 2)

