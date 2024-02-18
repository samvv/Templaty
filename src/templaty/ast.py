
import ast
from sys import setprofile
from typing import List, Optional, Any

from sweetener import BaseNode, Record, TextFile

class TextPos(Record):

    offset: int = 0
    line: int = 1
    column: int = 1

    def advance(self, text):
        for ch in text:
            if ch == '\n':
                self.line += 1
                self.column = 0
            else:
                self.column += 1
            self.offset += 1

class TextSpan(Record):
    file: TextFile
    start_pos: TextPos
    end_pos: TextPos

class Node(BaseNode):
    span: Optional[TextSpan] = None
    indent_level: Optional[int] = None

class Body(Node):
    elements: list['Statement']

class Pattern(Node):
    pass

class TuplePattern(Pattern):
    elements: List[Pattern]

class VarPattern(Pattern):
    name: str

class Expression(Node):
    pass

class IndexExpression(Expression):
    expression: Expression
    index: Expression

class SliceExpression(Expression):
    expression: Expression
    min: Optional[Expression]
    max: Optional[Expression]

class MemberExpression(Expression):
    expression: Expression
    members: List[str]

class VarRefExpression(Expression):
    name: str

class ConstExpression(Expression):
    value: Any

class CallExpression(Expression):
    operator: Expression
    operands: List[Expression]

class TupleExpression(Expression):
    elements: List[Expression]

class Statement(Node):
    pass

class TextStatement(Statement):
    text: str

class ExpressionStatement(Statement):
    expression: Expression

class CommentStatement(Statement):
    contents: str

class IfStatementCase(Node):
    test: Optional[Expression]
    body: Body

class IfStatement(Statement):
    cases: List[IfStatementCase]

class CodeBlock(Statement):
    module: ast.Module

class SetIndentStatement(Statement):
    level: Expression
    body: Body

class JoinStatement(Statement):
    pattern: Pattern
    expression: Expression
    separator: Expression
    body: Body

class ForInStatement(Statement):
    pattern: Pattern
    expression: Expression
    body: Body

class Template(Node):
    body: Body

