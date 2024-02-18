
from templaty.scanner import *

def test_scan_expression_followed_by_text():
    tokens = Scanner("#<expr_followed_by_text>", "The {{foo}} is cool!").scan()
    t0 = next(tokens)
    assert(t0.type == TEXT)
    t0 = next(tokens)
    assert(t0.type == OPEN_EXPRESSION_BLOCK)
    t1 = next(tokens)
    assert(t1.type == IDENTIFIER)
    t2 = next(tokens)
    assert(t2.type == CLOSE_EXPRESSION_BLOCK)
    t3 = next(tokens)
    assert(t3.type == TEXT)
    assert(t3.value == ' is cool!')

