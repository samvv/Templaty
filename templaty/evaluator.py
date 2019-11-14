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

from datetime import datetime
import ast

from .scanner import Position
from .ast import *
from .util import get_indentation, preorder, is_blank, starts_with_newline, ends_with_newline, remove_first_newline, to_snake_case
from .lines import *

class Env:

    def __init__(self, parent=None):
        self.parent = parent
        self._variables = {}

    def lookup(self, name):
        if name in self._variables:
            return self._variables[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise RuntimeError("Could not find '{}' in environment.".format(name))

    def set(self, name, value):
        self._variables[name] = value

    def fork(self):
        return Env(self)

def to_snake_case(name):
    if '-' in name:
        return name.replace('-', '_')
    else:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

DEFAULT_BUILTINS = {
        'range': lambda a, b: range(a, b),
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b,
        '%': lambda a, b: a % b,
        '==': lambda a, b: a == b,
        'snake': to_snake_case,
        'upper': lambda s: s.upper(),
        'lower': lambda s: s.lower(),
        '|>': lambda val, f: f(val)
        }

def is_inner_wrapped(stmt):
    return len(stmt.body) > 0 \
       and isinstance(stmt.body[0], TextStatement) \
       and starts_with_newline(stmt.body[0].text) \
       and isinstance(stmt.body[-1], TextStatement) \
       and ends_with_newline(stmt.body[-1].text)

def get_inner_indentation(node, at_blank_line=True):
    curr_indent = 0
    min_indent = None
    for node in preorder(node):
        if isinstance(node, TextStatement):
            for ch in node.text:
                if not at_blank_line:
                    if ch == '\n':
                        at_blank_line = True
                        curr_indent = 0
                else:
                    if is_blank(ch):
                        curr_indent += 1
                        continue
                    at_blank_line = ch == '\n'
                    if not at_blank_line and (min_indent is None or curr_indent < min_indent):
                        min_indent = curr_indent
            if min_indent is None:
                min_indent = 0
            return min_indent
        else:
            at_blank_line = False

INDENT_SET = 0
INDENT_ADD = 1

def evaluate(ast, ctx={}, indentation='  ', filename="#<anonymous>"):

    if isinstance(ast, str):
        from .scanner import Scanner
        from .parser import Parser
        sc = Scanner(filename, ast)
        p = Parser(sc)
        ast = p.parse_all()

    curr_indent = ''
    at_blank_line = True
    strip_next_newline = False

    def eval_code_expr(e, env):
        if isinstance(e, ConstExpression):
            return e.value
        elif isinstance(e, MemberExpression):
            out = eval_code_expr(e.expression, env)
            for name in e.path:
                out = out[name]
            return out
        elif isinstance(e, VarRefExpression):
            return env.lookup(e.name)
        elif isinstance(e, AppExpression):
            op = eval_code_expr(e.operator, env)
            args = list(eval_code_expr(arg, env) for arg in e.operands)
            if not callable(op):
                raise RuntimeError("Could not evaluate Templately expression: result is not applicable.".format(op))
            return op(*args)
        else:
            raise RuntimeError("Could not evaluate Templately expression: unknown expression {}.".format(e))

    def eval_statement_list(stmts, env):
        out = Lines()
        for stmt in stmts:
            out += eval_statement(stmt, env)
        return out

    def indent_depth(indentation):
        return len(indentation)

    def get_indentation_of_last_line(text):
        nonlocal at_blank_line
        last_indent = ''
        has_newline = False
        for ch in reversed(text):
            if ch == ' ':
                last_indent += ' '
            elif ch == '\n':
                has_newline = True
                at_blank_line = True
                break
            else:
                last_indent = ''
                at_blank_line = False
        if not has_newline:
            if at_blank_line:
                return curr_indent + last_indent
            else:
                return curr_indent
        else:
            return last_indent

    def eval_repeat(stmt, sep, env):
        out = Lines()
        rng = eval_code_expr(stmt.expression, env)
        count = max(rng) - min(rng) + 1
        env2 = env.fork()
        outer_indent = len(curr_indent)
        inner_indent = get_inner_indentation(stmt, at_blank_line)
        wrapped = is_inner_wrapped(stmt)
        for i in range(0, count):
            if i > 0: out += sep
            env2.set(stmt.pattern.name, i + min(rng))
            for j, child in enumerate(stmt.body):
                result = eval_statement(child, env2)
                if i == 0 and j == 0 and wrapped:
                    del result[0:1]
                if j == len(stmt.body) - 1 and wrapped:
                    del result[-(outer_indent+1):]
                out += result
        if wrapped:
            out.dedent()
        out.indent(' ' * outer_indent)
        del out[0:outer_indent]
        return out

    def eval_statement(stmt, env):

        nonlocal curr_indent, at_blank_line, strip_next_newline

        strip_curr_newline = strip_next_newline
        strip_next_newline = False

        if isinstance(stmt, TextStatement):
            curr_indent = get_indentation_of_last_line(stmt.text)
            text = stmt.text
            if strip_curr_newline:
                text = remove_first_newline(text)
            return split_lines(text)

        elif isinstance(stmt, IfStatement):
            for (cond, cons) in stmt.cases:
                if eval_code_expr(cond, env):
                    env2 = env.fork()
                    return eval_statement_list(cons, env2)
            if stmt.alternative is not None:
                env2 = env.fork()
                return eval_statement_list(stmt.alternative, env2)
            return Lines()

        elif isinstance(stmt, CodeBlock):
            exec(compile(stmt.module, filename=filename, mode='exec'), global_env._variables, env._variables)
            strip_next_newline = True

        elif isinstance(stmt, NoIndentStatement):
            strip_next_newline = True
            result = eval_statement_list(stmt.body, env)
            result.dedent()
            for line in result:
                if line.indent_override is None:
                    line.indent_override = 0
                    line
            return result

        elif isinstance(stmt, ExpressionStatement):
            return split_lines(str(eval_code_expr(stmt.expression, env)))

        elif isinstance(stmt, ForInStatement):
            return eval_repeat(stmt, Lines(), env)

        elif isinstance(stmt, JoinStatement):
            sep = split_lines(str(eval_code_expr(stmt.separator, env)))
            return eval_repeat(stmt, sep, env)

        else:
            raise TypeError("Could not evaluate statement: unknown statement {}.".format(stmt))

    global_env = Env()
    global_env.set('True', True)
    global_env.set('False', False)
    global_env.set('now', datetime.now().strftime("%b %d %Y %H:%M:%S"))
    for name, value in DEFAULT_BUILTINS.items():
        global_env.set(name, value)
    for name, value in ctx.items():
        global_env.set(name, value)

    return str(eval_statement_list(ast, global_env))

