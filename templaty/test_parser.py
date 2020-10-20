
import pytest

from templaty.scanner import Scanner
from templaty.parser import Parser, ParseError, ParseError, ParseError, ParseError
from templaty.ast import *

def test_parse_empty_code_block():
    sc = Scanner('#<empty_code_block>', "{! !}")
    p = Parser(sc)
    s = p.parse()
    assert(isinstance(s, CodeBlock))
    assert(len(s.module.body) == 0)

def test_parse_expr_code_block():
    sc = Scanner('#<empty_code_block>', "{! foo() !}")
    p = Parser(sc)
    s = p.parse()
    assert(isinstance(s, CodeBlock))
    (len(s.module.body), 1)

def test_parse_text_after_expr():
    sc = Scanner('#<text_after_expr>', 'The {{foo}} is cool!')
    p = Parser(sc)
    ast = list(p.parse_all())
    assert(ast[2].text == ' is cool!')

def test_parse_func_app_no_args():
    sc = Scanner('#<func_app_no_args>', "foo()", True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(isinstance(e.operator, VarRefExpression))
    assert(e.operator.name == 'foo')
    assert(len(e.operands) == 0)

def test_parse_func_app_one_arg():
    sc = Scanner('#<func_app_one_arg>', "foo(bar)", True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(isinstance(e.operator, VarRefExpression))
    assert(e.operator.name == 'foo')
    assert(len(e.operands) == 1)
    assert(isinstance(e.operands[0], VarRefExpression))
    assert(e.operands[0].name == 'bar')

def test_parse_func_app_many_args():
    sc = Scanner('#<func_app_many_args>', "foo(bar, 1, 2, 3)", True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(isinstance(e.operator, VarRefExpression))
    assert(e.operator.name == 'foo')
    assert(len(e.operands) == 4)
    assert(isinstance(e.operands[0], VarRefExpression))
    assert(e.operands[0].name == 'bar')
    assert(isinstance(e.operands[1], ConstExpression))
    assert(e.operands[1].value == 1)
    assert(isinstance(e.operands[2], ConstExpression))
    assert(e.operands[2].value == 2)
    assert(isinstance(e.operands[3], ConstExpression))
    assert(e.operands[3].value == 3)

def test_parse_for_in_statement():
    sc = Scanner('#<for_in_statement>', "{% for i in range(1, 10) %}Foo!{% endfor %}")
    p = Parser(sc)
    s = p.parse_statement()
    assert(isinstance(s, ForInStatement))
    assert(isinstance(s.pattern, VarPattern))
    assert(s.pattern.name == 'i')
    assert(isinstance(s.expression, AppExpression))
    assert(isinstance(s.expression.operator, VarRefExpression))
    assert(s.expression.operator.name == 'range')
    assert(len(s.expression.operands) == 2)
    assert(isinstance(s.expression.operands[0], ConstExpression))
    assert(s.expression.operands[0].value == 1)
    assert(isinstance(s.expression.operands[1], ConstExpression))
    assert(s.expression.operands[1].value == 10)
    assert(len(s.body) == 1)
    assert(isinstance(s.body[0], TextStatement))
    assert(s.body[0].text == 'Foo!')

def test_parse_single_if_statement():
    sc = Scanner('#<if_statement>', "{% if somevar %}Foo!{% endif %}")
    p = Parser(sc)
    s = p.parse_statement()
    assert(isinstance(s, IfStatement))
    assert(len(s.cases) == 1)
    case0 = s.cases[0]
    assert(isinstance(case0.test, VarRefExpression))
    assert(case0.test.name == 'somevar')
    assert(len(case0.cons) == 1)
    assert(isinstance(case0.cons[0], TextStatement))
    assert(case0.cons[0].text == 'Foo!')

def test_parse_fail_parse_close_delimiter():
    sc1 = Scanner('#<wrong_for_endif>', "{% for i in range(1, 10) %}Foo!{% endif %}")
    p1 = Parser(sc1)
    with pytest.raises(ParseError):
        p1.parse_statement()
    sc2 = Scanner('#<wrong_for_for>', "{% for i in range(1, 20) %}Foo!{% for %}")
    p2 = Parser(sc2)
    with pytest.raises(ParseError):
        p2.parse_statement()
    sc3 = Scanner('#<wrong_if_endfor>', "{% if somevmar %}Foo!{% endfor %}")
    p3 = Parser(sc3)
    with pytest.raises(ParseError):
        p3.parse_statement()

def test_parse_string_lit():
    sc = Scanner('#<string_lit>', "'Hello!'", True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, ConstExpression))
    assert(e.value == 'Hello!')

def test_parse_simple_add():
    sc = Scanner('#<simple_add>', 'a + b', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(len(e.operands) == 2)
    assert(isinstance(e.operands[0], VarRefExpression))
    assert(e.operands[0].name == 'a')
    assert(isinstance(e.operands[1], VarRefExpression))
    assert(e.operands[1].name == 'b')

def test_parse_nested_add():
    sc = Scanner('#<nested_add>', '(a + b) + c', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(len(e.operands) == 2)
    arg1 = e.operands[0]
    assert(isinstance(arg1, AppExpression))
    assert(arg1.operands[0].name == 'a')
    assert(arg1.operands[1].name == 'b')
    arg2 = e.operands[1]
    assert(isinstance(arg2, VarRefExpression))
    assert(arg2.name == 'c')

def test_parse_binary_operator_precedence1():
    sc = Scanner('#<binary_operator_precedence1>', 'a * b + c', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(len(e.operands) == 2)
    arg1 = e.operands[0]
    assert(isinstance(arg1, AppExpression))
    assert(arg1.operands[0].name == 'a')
    assert(arg1.operands[1].name == 'b')
    arg2 = e.operands[1]
    assert(isinstance(arg2, VarRefExpression))
    assert(arg2.name == 'c')

def test_parse_binary_operator_precedence2():
    sc = Scanner('#<binary_operator_precedence2>', 'a + b * c', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(len(e.operands) == 2)
    arg1 = e.operands[0]
    assert(isinstance(arg1, VarRefExpression))
    assert(arg1.name == 'a')
    arg2 = e.operands[1]
    assert(isinstance(arg2, AppExpression))
    assert(arg2.operands[0].name == 'b')
    assert(arg2.operands[1].name == 'c')

def test_parse_binary_operator_precedence3():
    sc = Scanner('#<binary_operator_precedence3>', 'a * b * c', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(len(e.operands) == 2)
    arg1 = e.operands[0]
    assert(isinstance(arg1, AppExpression))
    assert(arg1.operands[0].name == 'a')
    assert(arg1.operands[1].name == 'b')
    arg2 = e.operands[1]
    assert(isinstance(arg2, VarRefExpression))
    assert(arg2.name == 'c')

def test_parse_binary_operator_precedence4():
    sc = Scanner('#<binary_operator_precedence4>', 'a ** b ** c', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))
    assert(len(e.operands) == 2)
    arg1 = e.operands[0]
    assert(isinstance(arg1, VarRefExpression))
    assert(arg1.name == 'a')
    arg2 = e.operands[1]
    assert(isinstance(arg2, AppExpression))
    assert(arg2.operands[0].name == 'b')
    assert(arg2.operands[1].name == 'c')

def test_parse_not_operator():
    sc = Scanner('#<not_operator>', 'not a', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, AppExpression))

def test_parse_simple_member_access():
    sc = Scanner('#<member_access>', 'foo.bar', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, MemberExpression))
    assert(isinstance(e.expression, VarRefExpression))
    assert(e.expression.name == 'foo')
    assert(len(e.members) == 1)
    assert(e.members[0] == 'bar')

def test_parse_complex_expression():
    sc = Scanner('#<member_access>', '(1 + 2).bar.baz.bax', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, MemberExpression))
    assert(isinstance(e.expression, AppExpression))
    assert(isinstance(e.expression.operator, VarRefExpression))
    assert(e.expression.operator.name == '+')
    assert(len(e.expression.operands) == 2)
    assert(isinstance(e.expression.operands[0], ConstExpression))
    assert(e.expression.operands[0].value == 1)
    assert(isinstance(e.expression.operands[1], ConstExpression))
    assert(e.expression.operands[1].value == 2)
    assert(len(e.members) == 3)
    assert(e.members[0] == 'bar')
    assert(e.members[1] == 'baz')
    assert(e.members[2] == 'bax')

def test_parse_simple_index():
    sc = Scanner("#<simple_index>", 'foo[2]', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, IndexExpression))
    assert(isinstance(e.expression, VarRefExpression))
    assert(e.expression.name == 'foo')
    assert(isinstance(e.index, ConstExpression))
    assert(e.index.value == 2)

def test_parse_simple_slice():
    sc = Scanner("#<simple_slice>", 'foo[1:2]', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, SliceExpression))
    assert(isinstance(e.expression, VarRefExpression))
    assert(e.expression.name == 'foo')
    assert(isinstance(e.min, ConstExpression))
    assert(e.min.value == 1)
    assert(isinstance(e.max, ConstExpression))
    assert(e.max.value == 2)

def test_parse_complex_access():
    sc = Scanner("#<complex_access>", 'foo[1:2][3].bar[4]', True)
    p = Parser(sc)
    e = p.parse_expression()
    assert(isinstance(e, IndexExpression))
    assert(isinstance(e.index, ConstExpression))
    assert(e.index.value == 4)
    e1 = e.expression
    assert(isinstance(e1, MemberExpression))
    assert(e1.members[0] == 'bar')
    e2 = e1.expression
    assert(isinstance(e2, IndexExpression))
    assert(isinstance(e2.index, ConstExpression))
    assert(e2.index.value == 3)
    e3 = e2.expression
    assert(isinstance(e3, SliceExpression))
    assert(isinstance(e3.min, ConstExpression))
    assert(e3.min.value == 1)
    assert(isinstance(e3.max, ConstExpression))
    assert(e3.max.value == 2)
    e4 = e3.expression
    assert(isinstance(e4, VarRefExpression))
    assert(e4.name == 'foo')

