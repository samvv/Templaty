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
import re

from .scanner import Position
from .ast import *
from .util import get_indentation, preorder, is_blank, starts_with_newline, ends_with_newline, is_empty, escape

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

def is_inner_wrapped(body):
    return len(body) > 0 \
       and isinstance(body[0], TextStatement) \
       and starts_with_newline(body[0].text) \
       and isinstance(body[-1], TextStatement) \
       and ends_with_newline(body[-1].text)

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
                min_indent = curr_indent
            return min_indent
        else:
            at_blank_line = False

def find_trailing_newline(text):
    offset = len(text)-1
    for ch in reversed(text):
        if ch == '\n':
            return offset
        if not is_blank(ch):
            break
        offset -= 1
    return len(text)

def evaluate(ast, ctx={}, indentation='  ', filename="#<anonymous>"):

    if isinstance(ast, str):
        from .scanner import Scanner
        from .parser import Parser
        sc = Scanner(filename, ast)
        p = Parser(sc)
        ast = list(p.parse_all())

    curr_indent = ''
    at_blank_line = True
    out = Lines()

    def eval_code_expr(e, env):
        if isinstance(e, ConstExpression):
            return e.value
        elif isinstance(e, IndexExpression):
            val = eval_code_expr(e.expression, env)
            index = eval_code_expr(e.index, env)
            return val[index]
        elif isinstance(e, SliceExpression):
            val = eval_code_expr(e.expression, env)
            low = eval_code_expr(e.min, env)
            high = eval_code_expr(e.max, env)
            return val[low:high]
        elif isinstance(e, MemberExpression):
            out = eval_code_expr(e.expression, env)
            for name in e.path:
                out = getattr(out, name)
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
        result = Lines()
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            last_indent = len(curr_indent)
            prev_line_blank = at_blank_line
            next_line_blank = i == len(stmts)-1 or (isinstance(stmts[i+1], TextStatement) and starts_with_newline(stmts[i+1].text))
            iter_result = eval_statement(stmt, env)
            if not isinstance(stmt, TextStatement) \
                    and not isinstance(stmt, ExpressionStatement) \
                    and prev_line_blank \
                    and next_line_blank:
                if last_indent > 0:
                    del result[-last_indent:]
                if len(iter_result) == 0:
                    del result[-1:]
            result += iter_result
            i += 1
        return result

    def indent_depth(indentation):
        return len(indentation)

    def update_locals(text):
        nonlocal at_blank_line, curr_indent
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
                curr_indent = curr_indent + last_indent
        else:
            curr_indent = last_indent

    def eval_repeat(stmt, sep, env):
        result = Lines()
        iterable = eval_code_expr(stmt.expression, env)
        elements = list(iterable)
        env2 = env.fork()
        outer_indent = len(curr_indent)
        inner_indent = get_inner_indentation(stmt, at_blank_line)
        wrapped = is_inner_wrapped(stmt.body)
        for i, element in enumerate(elements):
            env2.set(stmt.pattern.name, element)
            env2.set('index', i)
            iter_result = eval_statement_list(stmt.body, env2)
            if wrapped:
                # remove first newline for i > 0
                # rest will be removed by dedent()
                if i > 0:
                    del iter_result[0:1]
                # we're wrapped, so insert sep somewhere
                # before the last newline is added
                if i < len(elements)-1:
                    last_newline = find_trailing_newline(str(iter_result))
                    iter_result.insert_at(last_newline, sep)
            else:
                if i < len(elements)-1:
                    iter_result += sep
            result += iter_result
        if wrapped:
            result.dedent()
            del result[0:1]
            del result[-1:]
        result.indent(' ' * outer_indent)
        return result


    def eval_statement(stmt, env):

        nonlocal curr_indent, at_blank_line, out

        if isinstance(stmt, TextStatement):
            update_locals(stmt.text)
            text = stmt.text
            result = split_lines(text)
            out += result 
            return result

        elif isinstance(stmt, IfStatement):
            outer_indent = len(curr_indent)
            for (cond, cons) in stmt.cases:
                if eval_code_expr(cond, env):
                    env2 = env.fork()
                    result = eval_statement_list(cons, env2)
                    if is_inner_wrapped(cons):
                        result.dedent()
                        del result[0:1]
                        del result[-1:]
                    result.indent(' ' * outer_indent)
                    out += result
                    return result
            if stmt.alternative is not None:
                env2 = env.fork()
                result = eval_statement_list(stmt.alternative, env2)
                if is_inner_wrapped(stmt.alternative):
                    result.dedent()
                    del result[0:1]
                    del result[-1:]
                result.indent(' ' * outer_indent)
                out += result
                return result
            return Lines()

        elif isinstance(stmt, CodeBlock):
            exec(compile(stmt.module, filename=filename, mode='exec'), global_env._variables, env._variables)
            return Lines()

        elif isinstance(stmt, SetIndentStatement):
            outer_indent = len(curr_indent)
            inner_indent = get_inner_indentation(stmt)
            indent_override = eval_code_expr(stmt.level, env)
            result = eval_statement_list(stmt.body, env)
            if is_inner_wrapped(stmt.body):
                result.dedent()
                del result[0:1]
                del result[-1:]
            result.indent(' ' * outer_indent)
            for line in result.get_lines():
                if line.indent_override is None:
                    line.indent_override = indent_override
            out += result
            return result

        elif isinstance(stmt, ExpressionStatement):
            result = split_lines(str(eval_code_expr(stmt.expression, env)))
            out += result
            return result

        elif isinstance(stmt, ForInStatement):
            result = eval_repeat(stmt, Lines(), env)
            out += result
            return result

        elif isinstance(stmt, JoinStatement):
            sep = split_lines(str(eval_code_expr(stmt.separator, env)))
            result = eval_repeat(stmt, sep, env)
            out += result
            return result

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

    output = ''
    res = eval_statement_list(ast, global_env)
    lines = res._lines
    i = 0

    while i < len(lines):

        indent_override = lines[i].indent_override

        # look ahead to see if this line or the next may contain
        # an indent_override flag
        j = i + 1
        while j < len(lines) and lines[j].join_with_next:
            if lines[j].indent_override is not None:
                indent_override = lines[j].indent_override
                break
            j += 1

        # no indent_override means there is no
        # special processing that has to take place
        if indent_override is None:
            output += str(lines[i])

        else:

            curr_indent_override = indent_override
            k = 0

            while i < len(lines):

                # pass through any characters that
                # are accepted by curr_indent_override
                while k < len(lines[i].text):
                    ch = lines[i].text[k]
                    if curr_indent_override == 0:
                        break
                    elif is_blank(ch):
                        curr_indent_override -= 1
                        output += ch
                        k += 1
                    else:
                        output += ' ' * curr_indent_override
                        break

                # FIXME currently no code requires this
                # if the line was not long enough and the next line might still
                # contain indentation, then now is the time to process it
                #  if curr_indent_override > 0:
                #      i += 1
                #      continue

                # skip any characters that are remaining
                # because they are excess indentation
                while k < len(lines[i].text) and is_blank(lines[i].text[k]):
                    k += 1

                # now the real string is added
                output += lines[i].text[k:]

                # finish off unless we have to append more lines
                if not lines[i].join_with_next:
                    output += '\n'
                    break

                curr_indent_override = indent_override
                i += 1

        i += 1

    return output


