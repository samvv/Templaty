
import gast
from typing import List, Optional, Any, Tuple

from .util import BaseNode

class Node(BaseNode):
    pass

class Pattern(Node):
    pass

class VarPattern(Pattern):
    name: str

class Expression(Node):
    pass

class MemberExpression(Expression):
    expression: Expression
    path: List[str]

class VarRefExpression(Expression):
    name: str

class ConstExpression(Expression):
    value: Any

class AppExpression(Expression):
    operator: Expression
    operands: List[Expression]

class Statement(Node):
    pass

class TextStatement(Statement):
    text: str

class ExpressionStatement(Statement):
    expression: Expression

class IfStatement(Statement):
    cases: List[Tuple[Expression, List[Statement]]]
    alternative: Optional[List[Statement]]

class CodeBlock(Statement):
    module: gast.Module

class NoIndentStatement(Statement):
    body: List[Statement]

class JoinStatement(Statement):
    pattern: Pattern
    expression: Expression
    separator: Expression
    body: List[Statement]

class ForInStatement(Statement):
    pattern: Pattern
    expression: Expression
    body: List[Statement]

def set_all_parents(node, parent=None):
    node.parent = parent
    for child in node.get_child_nodes():
        set_all_parents(child, node)

