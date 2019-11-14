# Copyright 2019 Sam Vervaeck
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
from typing import List, Optional, Any, Tuple, Union

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
    module: ast.Module

class SetIndentStatement(Statement):
    level: int
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

