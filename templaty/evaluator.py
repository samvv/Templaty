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
import re

from .ast import *
from .util import is_blank, starts_with_newline, ends_with_newline
from sweetener.node import preorder, set_parent_nodes

def indent(text, indentation, until_prev_line_blank=True, start=0):
    out = ''
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '\n':
            until_prev_line_blank = True
        elif until_prev_line_blank and not is_blank(ch):
            out += indentation
            until_prev_line_blank = False
        out += ch
    return out

def get_indentation(text, until_prev_line_blank=True, start=0):
    min_indent = None
    curr_indent = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '\n':
            until_prev_line_blank = True
            curr_indent = 0
        elif is_blank(ch):
            if until_prev_line_blank:
                curr_indent += 1
        else:
            if until_prev_line_blank:
                if min_indent is None or curr_indent < min_indent:
                    min_indent = curr_indent
                until_prev_line_blank = False
    if min_indent is None:
        min_indent = 0
    return min_indent

def dedent(text, until_prev_line_blank=True, indentation=None, start=0):
    out = ''
    if indentation is None:
        indentation = get_indentation(text, until_prev_line_blank=until_prev_line_blank, start=start)
    curr_indent = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == '\n':
            until_prev_line_blank = True
            curr_indent = 0
            out += ch
        elif is_blank(ch):
            if until_prev_line_blank:
                curr_indent += 1
                if curr_indent > indentation:
                    out += ch
            else:
                out += ch
        else:
            if until_prev_line_blank:
                until_prev_line_blank = False
            out += ch
        i += 1
    return out

# def redent(text, indentation, until_prev_line_blank=True):
#     return indent(dedent(text, until_prev_line_blank), indentation, until_prev_line_blank)

def skip(iterator, count):
    for _i in range(0, count):
        next(iterator)
    return iterator

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

def to_camel_case(name, first_char_lowercase=False):
    result = re.sub(r'[-_]', '', name.title())
    return result[0].lower() + result[1:] if first_char_lowercase else result

DEFAULT_BUILTINS = {
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

def is_inner_wrapped(node):
    if isinstance(node, IfStatement):
        return all(is_inner_wrapped(case) for case in node.cases)
    elif isinstance(node, CodeBlock) \
        or isinstance(node, TextStatement) \
        or isinstance(node, ExpressionStatement):
        return False
    elif isinstance(node, ForInStatement) \
        or isinstance(node, JoinStatement) \
        or isinstance(node, SetIndentStatement) \
        or isinstance(node, IfStatementCase) \
        or isinstance(node, Template):
        body = node.body
    else:
        raise RuntimeError(f'unable to deduce whether {node} is wrapped or not')
    return len(body) > 0 \
       and isinstance(body[0], TextStatement) \
       and starts_with_newline(body[0].text) \
       and isinstance(body[-1], TextStatement) \
       and ends_with_newline(body[-1].text)

def is_outer_wrapped(node: Node):
    if isinstance(node, IfStatementCase):
        node = node.parent
    if node.prev_child is not None:
        if not isinstance(node.prev_child, TextStatement):
            return False
        if not (ends_with_newline(node.prev_child.text) \
                or (isinstance(node.parent, Template) and is_blank(node.prev_child.text))):
            return False
    if node.next_child is not None:
        if not isinstance(node.next_child, TextStatement):
            return False
        if not (starts_with_newline(node.next_child.text) \
                or (isinstance(node.parent, Template) and is_blank(node.next_child.text))):
            return False
    return True

def is_wrapped(node):
    if isinstance(node, Template):
        return False
    if isinstance(node, ExpressionStatement):
        return False
    return is_inner_wrapped(node) and is_outer_wrapped(node)

def expand_body(node):
    if isinstance(node, ForInStatement) \
        or isinstance(node, JoinStatement) \
        or isinstance(node, SetIndentStatement) \
        or isinstance(node, IfStatementCase):
        for i in range(0, len(node.body)):
            yield ['body', i], node.body[i]

def get_inner_indentation(node, after_blank_line=True):
    curr_indent = 0
    min_indent = None
    for child in skip(preorder(node, expand=expand_body), 1):
        if isinstance(child, TextStatement):
            for ch in child.text:
                if ch == '\n':
                    after_blank_line = True
                    curr_indent = 0
                elif is_blank(ch):
                    if after_blank_line:
                        curr_indent += 1
                else:
                    if after_blank_line:
                        after_blank_line = False
                        if min_indent is None or curr_indent < min_indent:
                            min_indent = curr_indent
        else:
            if after_blank_line:
                after_blank_line = False
                if min_indent is None or curr_indent < min_indent:
                    min_indent = curr_indent
    return curr_indent if min_indent is None else min_indent 

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

def find_first_line(text):
    for i in range(0, len(text)):
        if text[i] == '\n':
            return i
    return 0

def find_trailing_newline(text, start=None):
    if start is None:
        start = len(text)-1
    offset = start
    for ch in reversed(text[:start+1]):
        if ch == '\n':
            return offset
        if not is_blank(ch):
            break
        offset -= 1
    return len(text)

class Core(Record):
    pass

class Join(Core):
    separator: Optional[str]
    elements: List[Core]

class Text(Core):
    value: str

class SetIndent(Core):
    indentation: str
    expression: Core

def evaluate(ast, ctx={}, indentation='  ', filename="#<anonymous>"):

    if isinstance(ast, str):
        from .scanner import Scanner
        from .parser import Parser
        sc = Scanner(filename, ast)
        p = Parser(sc)
        ast = p.parse_all()
        set_parent_nodes(ast)

    out = ''
    indent_level = 0
    indent_override = None
    curr_indent = ''
    after_blank_line = True
    skip_next_chars = 0
    written_curr_indent = 0
    written_after_blank_line = True

    def write_or_skip(text):
        nonlocal out, skip_next_chars
        if skip_next_chars < len(text):
            out += text[skip_next_chars:]
            skip_next_chars = 0
        else:
            skip_next_chars -= len(text)

    def write(text, undent):
        nonlocal out, written_after_blank_line, written_curr_indent
        for ch in text:
            if ch == '\n':
                written_after_blank_line = True
                write_or_skip(ch)
                written_curr_indent = 0
            elif is_blank(ch):
                if written_after_blank_line:
                    written_curr_indent += 1
                else:
                    write_or_skip(ch)
            else:
                if written_after_blank_line:
                    write_or_skip(' ' * (indent_override if indent_override is not None else max(0, written_curr_indent - undent)))
                written_after_blank_line = False
                write_or_skip(ch)

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
            for name in e.members:
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

    def eval_statement_list(stmts, env, parent, indent_delta):

        nonlocal skip_next_chars, out

        parent_wrapped = is_wrapped(parent)
        outer_indent = parent.span.start_pos.column-1 - indent_delta
        inner_indent = (get_inner_indentation(parent, after_blank_line) - (parent.span.start_pos.column-1)) if parent_wrapped else 0
        all_empty = True

        if parent_wrapped:
            skip_next_chars += 1

        for i, stmt in enumerate(stmts):
            if i > 0 and is_wrapped(stmts[i-1]):
                skip_next_chars += 1
            is_empty = eval_statement(stmt, env, indent_delta + inner_indent)
            if is_empty:
                all_empty = False

        # if all_empty and is_outer_wrapped(parent):
        #     skip_next_chars += 1

        return all_empty

    def update_locals(text):
        nonlocal after_blank_line, curr_indent
        last_indent = ''
        has_newline = False
        for ch in reversed(text):
            if ch == ' ':
                last_indent += ' '
            elif ch == '\n':
                has_newline = True
                after_blank_line = True
                break
            else:
                last_indent = ''
                after_blank_line = False
        if not has_newline:
            if after_blank_line:
                curr_indent = curr_indent + last_indent
        else:
            curr_indent = last_indent

    def assign_patterns(env, pattern, value):
        if isinstance(pattern, VarPattern):
            env.set(pattern.name, value)
        elif isinstance(pattern, TuplePattern):
            for patt_2, val_2 in zip(pattern.elements, value):
                assign_patterns(env, patt_2, val_2)
        else:
            raise RuntimeError(f'could not evaluate pattern {pattern}')

    def eval_repeat(stmt, sep, env, indent_delta):

        nonlocal out

        all_empty = False
        prev_empty = True
        written_separator = False

        # the actual Python value that is going to be iterated over
        iterable = eval_code_expr(stmt.expression, env)

        # we 'fork' the env so that variables defined inside it do not leak to
        # the parent env
        # this is slightly different than the way Python works, but helps in
        # avoiding unexpected results due to variable name collision
        env2 = env.fork()

        for i, element in enumerate(iterable):

            # set up some environment variables
            # specific to the current iteration
            assign_patterns(env2, stmt.pattern, element)
            env2.set('index', i)

            if sep is not None and not prev_empty and not written_separator:
                written_separator = True
                i = find_trailing_newline(out)
                out = out[:i] + sep + out[i:]

            # generate the actual text
            prev_empty = eval_statement_list(stmt.body, env2, stmt, indent_delta)

            if not prev_empty:
                all_empty = False
                written_separator = False

        return all_empty

    def eval_statement(stmt, env, indent_delta):

        nonlocal curr_indent, after_blank_line, skip_next_chars, indent_override

        if not isinstance(stmt, TextStatement):
            after_blank_line = False

        if isinstance(stmt, TextStatement):
            update_locals(stmt.text)
            write(stmt.text, indent_delta)
            return is_blank(stmt.text)

        elif isinstance(stmt, IfStatement):
            for case in stmt.cases:
                if case.test is None or eval_code_expr(case.test, env):
                    env2 = env.fork()
                    return eval_statement_list(case.body, env2, case, indent_delta)
            return True

        elif isinstance(stmt, CodeBlock):
            exec(compile(stmt.module, filename=filename, mode='exec'), global_env._variables, env._variables)
            if is_outer_wrapped(stmt):
                skip_next_chars += 1
            return True

        elif isinstance(stmt, SetIndentStatement):
            old_indent_override = indent_override
            indent_override = eval_code_expr(stmt.level, env)
            is_empty = eval_statement_list(stmt.body, env, stmt, indent_delta)
            indent_override = old_indent_override
            return is_empty

        elif isinstance(stmt, ExpressionStatement):
            text = str(eval_code_expr(stmt.expression, env))
            if is_outer_wrapped(stmt):
                text = indent(
                    dedent(text),
                    ' ' * len(curr_indent), False
                    )
            # FIXME This len(curr_indent) - indent_delta looks suspicious
            write(text, indent_delta)
            return is_blank(text)

        elif isinstance(stmt, ForInStatement):
            return eval_repeat(stmt, None, env, indent_delta)

        elif isinstance(stmt, JoinStatement):
            sep = str(eval_code_expr(stmt.separator, env))
            return eval_repeat(stmt, sep, env, indent_delta)

        else:
            raise TypeError("Could not evaluate statement: unknown statement {}.".format(stmt))

    def _do_indent():
        nonlocal curr_indent, indent_level
        indent_level += 1
        curr_indent += indentation

    def _do_dedent():
        nonlocal curr_indent, indent_level
        indent_level -= 1
        curr_indent = curr_indent[0:-len(indentation)]

    def _do_write(text):
        write_or_skip(text)

    global_env = Env()
    global_env.set('True', True)
    global_env.set('False', False)
    global_env.set('now', datetime.now().strftime("%b %d %Y %H:%M:%S"))
    for name, value in DEFAULT_BUILTINS.items():
        global_env.set(name, value)
    for name, value in ctx.items():
        global_env.set(name, value)
    global_env.set('indent', _do_indent)
    global_env.set('dedent', _do_dedent)
    global_env.set('write', _do_write)

    eval_statement_list(ast.body, global_env, ast, 0)
    return out


