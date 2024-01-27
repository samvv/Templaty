
from .ast import *
from .outline import dedent

def test_deden_text():
    node = TextStatement('''
    foo
      bar
    baz
''')
    dedent(node, 4)
    assert(node.text == '''
foo
  bar
baz
''')

def test_partial_dedent_text():
    node = TextStatement('''
    foo
      bar
    baz
''')
    dedent(node, 3)
    assert(node.text == '''
 foo
   bar
 baz
''')

def test_dedent_compound():
    node = Body([
        TextStatement('\n    '),
        ExpressionStatement(VarRefExpression('foo')),
        TextStatement('\n      '),
        ExpressionStatement(VarRefExpression('bar')),
        TextStatement('\n    '),
        ExpressionStatement(VarRefExpression('baz')),
    ])
    dedent(node, 4)
    assert(isinstance(node.elements[0], TextStatement))
    assert(node.elements[0].text == '\n')
    assert(isinstance(node.elements[2], TextStatement))
    assert(node.elements[2].text == '\n  ')
    assert(isinstance(node.elements[4], TextStatement))
    assert(node.elements[4].text == '\n')

def test_partial_dedent_compound():
    node = Body([
        TextStatement('\n    '),
        ExpressionStatement(VarRefExpression('foo')),
        TextStatement('\n      '),
        ExpressionStatement(VarRefExpression('bar')),
        TextStatement('\n    '),
        ExpressionStatement(VarRefExpression('baz')),
    ])
    dedent(node, 3)
    assert(isinstance(node.elements[0], TextStatement))
    assert(node.elements[0].text == '\n ')
    assert(isinstance(node.elements[2], TextStatement))
    assert(node.elements[2].text == '\n   ')
    assert(isinstance(node.elements[4], TextStatement))
    assert(node.elements[4].text == '\n ')

