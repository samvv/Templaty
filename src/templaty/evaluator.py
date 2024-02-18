# Copyright 2024 Sam Vervaeck
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

from typing import Any
import math
from sweetener import set_parent_nodes
from datetime import datetime

from .outline import outline
from .ast import *
from .util import is_blank, is_whitespace, to_snake_case, to_camel_case
from .lines import Lines, Line, insert_after, render, rfind, size

class Env:

    def __init__(self, parent: 'Env | None' = None) -> None:
        self.parent = parent
        self._mapping: dict[str, Any] = {}

    def set(self, name: str, value: Any) -> None:
        self._mapping[name] = value

    def update(self, mapping: dict[str, Any]) -> None:
        self._mapping.update(mapping)

    def __contains__(self, name: str) -> bool:
        curr = self
        while True:
            if name in curr._mapping:
                return True
            curr = curr.parent
            if curr is None:
                break
        return False

    def lookup(self, name: str) -> Any | None:
        curr = self
        while True:
            if name in curr._mapping:
                return curr._mapping[name]
            curr = curr.parent
            if curr is None:
                break

    def to_dict(self) -> dict[str, Any]:
        out = {}
        curr = self
        while True:
            out.update(curr._mapping)
            curr = curr.parent
            if curr is None:
                break
        return out

DEFAULT_BUILTINS = {
    'None': None,
    'True': True,
    'False': False,
    'repr': repr,
    'zip': zip,
    'enumerate': enumerate,
    'isinstance': isinstance,
    'range': range,
    'reversed': reversed,
    '+': lambda a, b: a + b,
    '-': lambda a, b: a - b,
    '*': lambda a, b: a * b,
    '/': lambda a, b: a / b,
    '%': lambda a, b: a % b,
    '==': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
    'camel': to_camel_case,
    'snake': to_snake_case,
    'upper': lambda s: s.upper(),
    'lower': lambda s: s.lower(),
    '|>': lambda val, f: f(val),
    'in': lambda key, val: key in val
    }

def evaluate(template: str | Template, ctx: dict[str, Any] = {}, indentation = '  ', filename = "#<anonymous>"):

    def bind_pattern(pattern: Pattern, value: Any, env: Env) -> None:
        if isinstance(pattern, VarPattern):
            env.set(pattern.name, value)
            return
        if isinstance(pattern, TuplePattern):
            for i, element in enumerate(pattern.elements):
                bind_pattern(element, value[i], env)
            return
        raise RuntimeError(f'unexpected node {pattern}')

    def eval_expr(expr: Expression, env: Env) -> Any:
        if isinstance(expr, ConstExpression):
            return expr.value
        elif isinstance(expr, IndexExpression):
            val = eval_expr(expr.expression, env)
            index = eval_expr(expr.index, env)
            return val[index]
        elif isinstance(expr, SliceExpression):
            val = eval_expr(expr.expression, env)
            low = eval_expr(expr.min, env)
            high = eval_expr(expr.max, env)
            return val[low:high]
        elif isinstance(expr, MemberExpression):
            out = eval_expr(expr.expression, env)
            for name in expr.members:
                out = getattr(out, name)
            return out
        elif isinstance(expr, VarRefExpression):
            if expr.name in env:
                return env.lookup(expr.name)
            if expr.name == 'globals':
                return lambda: global_env
            elif expr.name == 'locals':
                return lambda: env
            else:
                message = ''
                span = expr.span
                if span is not None:
                    message += f'{span.file.name}:{span.start_pos.line}:{span.start_pos.column}: '
                message += f"variable '{expr.name}' is not defined"
                raise RuntimeError(message)
        elif isinstance(expr, CallExpression):
            op = eval_expr(expr.operator, env)
            args = list(eval_expr(arg, env) for arg in expr.operands)
            if not callable(op):
                raise RuntimeError("Could not evaluate Templately expression: result is not applicable.".format(op))
            return op(*args)
        else:
            raise RuntimeError("Could not evaluate Templately expression: unknown expression {}.".format(expr))

    def wrap(text: str) -> Lines:
        if not text:
            return []
        lines = list(Line(text) for text in text.splitlines())
        if text[-1] != '\n':
            lines[-1].end = False
        return lines

    at_blank_line = True
    curr_indent = 0

    def advance(text: str) -> None:
        nonlocal at_blank_line, curr_indent
        for ch in text:
            if ch == '\n':
                at_blank_line = True
                curr_indent = 0
            else:
                if at_blank_line:
                    if is_blank(ch):
                        curr_indent += 1
                    else:
                        at_blank_line = False


    def dedent(lines: Lines, at_blank_line=True) -> None:
        indent_length = get_indentation(lines, at_blank_line)
        remaining = indent_length
        for line in lines:
            if at_blank_line:
                removed = min(remaining, len(line.text))
                line.text = line.text[removed:]
                remaining -= removed
            if line.end:
                at_blank_line = True 
                remaining = indent_length

    def remove_last_line(lines: Lines) -> None:
        k = len(lines)-1
        for line in reversed(lines):
            i = len(line.text)-1
            while i >= 0:
                if not is_blank(line.text[i]):
                    break
                i -= 1
            if i != -1:
                line.text = line.text[0:i+1]
                break
            line = lines[k]
            del lines[k]
            if line.end:
                break
            k -= 1

    def rtrim(lines: Lines) -> None:
        k = len(lines)-1
        for line in reversed(lines):
            i = len(line.text)-1
            while i >= 0:
                if not is_blank(line.text[i]):
                    break
                i -= 1
            if i == -1:
                del lines[k]
            else:
                line.text = line.text[0:i+1]
                break
            k -= 1

    def indent(lines: Lines, indent_level: int, at_blank_line=True) -> None:
        indentation = ' ' * indent_level
        for line in lines:
            if at_blank_line:
                if is_blank(line.text):
                    continue
                line.text = indentation + line.text
            at_blank_line = line.end

    def get_indentation(lines: Lines, at_blank_line=True, default_indent=0):
        min_indent = math.inf
        curr_indent = 0
        for line in lines:
            for ch in line.text:
                if not at_blank_line:
                    break
                if is_blank(ch):
                    curr_indent += 1
                else:
                    at_blank_line = False
            if line.end:
                if not at_blank_line and curr_indent < min_indent:
                    min_indent = curr_indent
                at_blank_line = True
                curr_indent = 0
        if min_indent == math.inf:
            return default_indent if at_blank_line else curr_indent 
        return min_indent

    def eval_loop(stmt: ForInStatement | JoinStatement, env: Env, sep: Expression | None = None) -> Lines:
            value = eval_expr(stmt.expression, env)
            sep_value = sep and eval_expr(sep, env)
            lines = []
            elements = list(value)
            results = []
            for i, element in enumerate(elements):
                inner_env = Env(env)
                inner_env.set('index', i)
                bind_pattern(stmt.pattern, element, inner_env)
                res = eval_stmt(stmt.body, inner_env)
                if size(res) > 0:
                    results.append(res)
            for i, res in enumerate(results):
                if sep_value and i < len(results)-1:
                    k = rfind(res, lambda ch: not is_whitespace(ch))
                    if k == -1:
                        k = size(res)
                    insert_after(res, k, wrap(str(sep_value)))
                lines.extend(res)
            return lines

    def eval_stmt(stmt: Node, env: Env) -> Lines:

        if isinstance(stmt, Body):
            out = []
            for stmt in stmt.elements:
                lines = eval_stmt(stmt, env)
                out.extend(lines)
            return out

        if isinstance(stmt, TextStatement):
            advance(stmt.text)
            return wrap(stmt.text)

        if isinstance(stmt, IfStatement):
            for case in stmt.cases:
                if case.test is None:
                    return eval_stmt(case.body, env)
                value = eval_expr(case.test, env)
                if value:
                    return eval_stmt(case.body, env)
            return []

        if isinstance(stmt, ForInStatement):
            return eval_loop(stmt, env)

        if isinstance(stmt, JoinStatement):
            return eval_loop(stmt, env, sep=stmt.separator)

        if isinstance(stmt, ExpressionStatement):
            value = eval_expr(stmt.expression, env)
            return wrap(str(value))

        if isinstance(stmt, SetIndentStatement):
            level = eval_expr(stmt.level, env)
            lines = eval_stmt(stmt.body, env)
            for line in lines:
                if line.indent_override is None:
                    line.indent_override = level
            return lines

        if isinstance(stmt, CodeBlock):
            globals = global_env.to_dict()
            locals = env.to_dict()
            exec(compile(stmt.module, filename=filename, mode='exec'), globals, locals)
            for k, v in locals.items():
                if k not in env or env.lookup(k) != v:
                    env.set(k, v)
            return []

        raise RuntimeError(f'unexpected node {stmt}')

    if isinstance(template, str):
        from .scanner import Scanner
        from .parser import Parser
        sc = Scanner(filename, template)
        p = Parser(sc)
        template = p.parse_all()
        set_parent_nodes(template)

    global_env = Env()
    global_env.update(DEFAULT_BUILTINS)
    global_env.update(ctx)
    global_env.set('now', datetime.now().strftime("%b %d %Y %H:%M:%S"))

    outline(template)
    lines = eval_stmt(template.body, global_env)

    out = ''
    for line in lines:
        if line.indent_override is not None:
            out += indentation * line.indent_override
        out += line.text
        if line.end:
            out += '\n'

    return out
