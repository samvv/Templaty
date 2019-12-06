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
        return None

    def __contains__(self, item):
        return self.lookup(item) is not None

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
        'snake': to_snake_case,
        'upper': lambda s: s.upper(),
        'lower': lambda s: s.lower(),
        '|>': lambda val, f: f(val),
        'in': lambda key, val: key in val
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

def remove_last_newlines(result, count):
    offset = len(result)-1
    while count > 0 and offset >= 0:
        ch = result[offset]
        if ch == '\n':
            count -= 1
        elif not is_blank(ch):
            break
        offset -= 1
    del result[offset+1:]

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
    blank_line_count = 0

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
            value = env.lookup(e.name)
            if value is not None:
                return value
            if e.name == 'globals':
                return lambda: global_env
            elif e.name == 'locals':
                return lambda: env
            else:
                raise RuntimeError(f"variable '{e.name}' is not defined")
        elif isinstance(e, AppExpression):
            op = eval_code_expr(e.operator, env)
            args = list(eval_code_expr(arg, env) for arg in e.operands)
            if not callable(op):
                raise RuntimeError("Could not evaluate Templately expression: result is not applicable.".format(op))
            return op(*args)
        else:
            raise RuntimeError("Could not evaluate Templately expression: unknown expression {}.".format(e))

    def eval_statement_list(stmts, env):

        # this variable will be returned once we've processed every statement
        result = Lines()

        for i, stmt in enumerate(stmts):

            last_indent = len(curr_indent)
            prev_line_blank = at_blank_line
            prev_blank_line_count = blank_line_count
            next_stmt = None if i == len(stmts)-1 else stmts[i+1]
            next_line_blank = next_stmt is not None and (isinstance(next_stmt, TextStatement) and starts_with_newline(next_stmt.text))

            wrapped, iter_result = eval_statement(stmt, env)

            # this condition will only be true if we're currently holding a
            # special statement (such as a for-block) that does not share its
            # line(s) with other statements
            if not isinstance(stmt, TextStatement) \
                    and not isinstance(stmt, ExpressionStatement) \
                    and prev_line_blank \
                    and next_line_blank:

                # if the statement was indented, we want to remove this leading
                # indentation because when wrapped, eval_statement will apply
                # its own indentation to each generated line
                if last_indent > 0 and wrapped:
                    del result[-last_indent:]

                # blocks that generated no content can safely be skipped
                # we do so by deleting the last newlines
                # we know the newlines are there because prev_line_blank is true
                # blank_line_count will contain the amount of newlines
                if len(iter_result) == 0:
                    remove_last_newlines(result, prev_blank_line_count)

            # we've finished processing this iter_result, so append it to the
            # final result
            result += iter_result

        return result


    def update_locals(text):
        nonlocal at_blank_line, blank_line_count, curr_indent
        last_indent = ''
        has_newline = False
        for ch in reversed(text):
            if ch == ' ':
                last_indent += ' '
            elif ch == '\n':
                has_newline = True
                blank_line_count += 1
                at_blank_line = True
                break
            else:
                last_indent = ''
                blank_line_count = 0
                at_blank_line = False
        if not has_newline:
            if at_blank_line:
                curr_indent = curr_indent + last_indent
        else:
            curr_indent = last_indent


    def eval_repeat(stmt, sep, env):

        # this variable will be returned once we're done iterating
        result = Lines()

        # the actual Python value that is going to be iterated over
        iterable = eval_code_expr(stmt.expression, env)

        # we 'fork' the env so that variables defined inside it do not leak to
        # the parent env
        # this is slightly different than the way Python works, but helps in
        # avoiding unexpected results due to variable name collision
        env2 = env.fork()

        outer_indent = len(curr_indent)
        inner_indent = get_inner_indentation(stmt, at_blank_line)
        wrapped = is_inner_wrapped(stmt.body)

        last_iter_result = None

        for i, element in enumerate(iterable):

            # set up some environment variables
            # specific to the current iteration
            env2.set(stmt.pattern.name, element)
            env2.set('index', i)

            # generate the actual text
            iter_result = eval_statement_list(stmt.body, env2)

            # blocks that generated no content other than the single newline
            # that is left after eval_statement_list can safely be skipped
            # FIXME this check might need to be fine-tuned
            if is_empty(str(iter_result)):
                continue

            if last_iter_result is not None:

                if wrapped:

                    # remove first newline
                    # rest of indentation will be removed by dedent()
                    del iter_result[0:1]

                    # we're wrapped, so insert sep somewhere
                    # before the last newline is added
                    last_newline = find_trailing_newline(str(last_iter_result))
                    last_iter_result.insert_at(last_newline, sep)

                else:
                    last_iter_result += sep

            # last_iter_result should now be finally ready to be appended
            # iter_result will become the new last_iter_result to be appended
            if last_iter_result is not None:
                result += last_iter_result
            last_iter_result = iter_result

        # we might have one last_iter_result left behind, so we make sure to
        # add it to the result as well
        if last_iter_result is not None:
            result += last_iter_result

        # just some regular post-processing on the result of this block to make
        # sure it aligns with the rest of the text
        if wrapped:
            result.dedent()
            del result[0:1]
            del result[-1:]
            result.indent(' ' * outer_indent)
        else:
            result.indent(' ' * outer_indent, start=result.find('\n'))

        return wrapped, result


    def eval_statement(stmt, env):

        nonlocal curr_indent, at_blank_line, blank_line_count

        if not isinstance(stmt, TextStatement):
            blank_line_count = 0

        if isinstance(stmt, TextStatement):
            update_locals(stmt.text)
            result = Lines(stmt.text)
            return False, result

        elif isinstance(stmt, IfStatement):

            outer_indent = len(curr_indent)

            for (cond, cons) in stmt.cases:

                if eval_code_expr(cond, env):

                    env2 = env.fork()

                    wrapped = is_inner_wrapped(cons)

                    result = eval_statement_list(cons, env2)

                    # just some regular post-processing on the result of this block to make
                    # sure it aligns with the rest of the text
                    if wrapped:
                        result.dedent()
                        del result[0:1]
                        del result[-1:]
                        result.indent(' ' * outer_indent)
                    else:
                        result.indent(' ' * outer_indent, start=result.find('\n'))

                    return wrapped, result

            if stmt.alternative is not None:

                env2 = env.fork()

                wrapped = is_inner_wrapped(stmt.alternative)

                result = eval_statement_list(stmt.alternative, env2)

                # just some regular post-processing on the result of this block to make
                # sure it aligns with the rest of the text
                if wrapped:
                    result.dedent()
                    del result[0:1]
                    del result[-1:]
                    result.indent(' ' * outer_indent)
                else:
                    result.indent(' ' * outer_indent, start=result.find('\n'))

                return wrapped, result

            # FIXME need to detect if this is acutally wrapped
            return True, Lines()

        elif isinstance(stmt, CodeBlock):
            exec(compile(stmt.module, filename=filename, mode='exec'), global_env._variables, env._variables)
            # FIXME need to detect if this is acutally wrapped
            return True, Lines()

        elif isinstance(stmt, SetIndentStatement):

            outer_indent = len(curr_indent)
            inner_indent = get_inner_indentation(stmt)
            indent_override = eval_code_expr(stmt.level, env)
            wrapped = is_inner_wrapped(stmt.body)

            result = eval_statement_list(stmt.body, env)

            # just some regular post-processing on the result of this block to make
            # sure it aligns with the rest of the text
            if wrapped:
                result.dedent()
                del result[0:1]
                del result[-1:]
                result.indent(' ' * outer_indent)
            else:
                result.indent(' ' * outer_indent, start=result.find('\n'))

            # apply the actual indent override by setting it on each line that
            # did not have an indent_override set from deeper blocks
            for line in result.get_lines():
                if line.indent_override is None:
                    line.indent_override = indent_override

            return wrapped, result

        elif isinstance(stmt, ExpressionStatement):
            result = Lines(str(eval_code_expr(stmt.expression, env)))
            # FIXME need to detect if this is acutally wrapped
            return True, result

        elif isinstance(stmt, ForInStatement):
            return eval_repeat(stmt, Lines(), env)

        elif isinstance(stmt, JoinStatement):
            sep = Lines(str(eval_code_expr(stmt.separator, env)))
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

    lines = eval_statement_list(ast, global_env)
    return apply_indent_override(lines)


