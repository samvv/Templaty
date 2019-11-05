
from textwrap import indent, dedent
from datetime import datetime
import math
from datetime import datetime
import re

from .ast import *

def starts_with_newline(text):
    for ch in text:
        if ch == '\n':
            return True
        if ch == ' ' or ch == '\t' or ch == '\r':
            continue
        break
    return False

def ends_with_newline(text):
    for ch in reversed(text):
        if ch == '\n':
            return True
        if ch == ' ' or ch == '\t' or ch == '\r':
            continue
        break
    return False

def remove_first_newline(text):
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '\n':
            i += 1
            break
        if not (ch == ' ' or ch == '\t'):
            return
        i += 1
    return text[i:]

def remove_last_newline(text):
    i = len(text)-1
    while i >= 0:
        ch = text[i]
        if ch == '\n':
            i -= 1
            break
        if not (ch == ' ' or ch == '\t'):
            return
        i -= 1
    return text[0:i+1]

# FIXME support tabs as well
def get_indentation(text):
    curr_indent = 0
    has_chars = False
    min_indent = math.inf
    for ch in text:
        if ch == '\n':
            if has_chars and curr_indent > 0:
                min_indent = min(min_indent, curr_indent)
            curr_indent = 0
            has_chars = False
        elif not has_chars:
            if ch == ' ':
                curr_indent += 1
            else:
                has_chars = True
    return min_indent if not math.isinf(min_indent) else curr_indent

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

def strip_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text

def count_newlines(text):
    count = 0
    for ch in text:
        if ch == '\n':
            count += 1
    return count

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

def evaluate(ast, ctx={}, indentation='  ', filename="#<anonymous>"):

    if isinstance(ast, str):
        from .scanner import Scanner
        from .parser import Parser
        sc = Scanner(filename, ast)
        p = Parser(sc)
        ast = p.parse_all()

    indent_override = 0
    curr_indent = ''
    at_blank_line = True

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
        out = ''
        for stmt in stmts:
            result = eval_statement(stmt, env)
            #  if not isinstance(stmt, TextStatement) and is_wrapped(stmt):
            #      result = remove_last_newline(result)
            out += result
        return out

    def eval_repeat(pattern, rng, body, sep=''):
        env2 = env.fork()
        out = ''
        block_indent = curr_indent
        is_wrapped = len(body) > 0 \
           and isinstance(body[0], TextStatement) \
           and starts_with_newline(body[0].text) \
           and isinstance(body[-1], TextStatement) \
           and ends_with_newline(body[-1].text)
        for i in rng:
            if i > 0: out += sep
            env2.set(pattern.name, i)
            children = list(body)
            temp_out = ''
            smallest_indent = math.inf
            for j, child in enumerate(children):
                result = eval_statement(child, env2)
                smallest_indent = min(smallest_indent, get_indentation(result))
                if j == 0 and is_wrapped: result = remove_first_newline(result)
                temp_out += result
            if count_newlines(temp_out) > 0 and not math.isinf(smallest_indent):
                indent_str = strip_prefix(indentation * max(0, smallest_indent - 1), block_indent)
                if i > 0 or is_wrapped:
                    indent_str = block_indent + indent_str
                temp_out = indent(dedent(temp_out), indent_str)
                if i == 0:
                    temp_out = strip_prefix(temp_out, block_indent)
            out += temp_out
        return remove_last_newline(out) if is_wrapped else out

    def eval_statement(stmt, env):

        nonlocal curr_indent

        if isinstance(stmt, TextStatement):
            last_indent = ''
            has_newline = False
            for ch in reversed(stmt.text):
                if ch == ' ':
                    last_indent += ' '
                elif ch == '\n':
                    has_newline = True
                    break
                else:
                    last_indent = ''
            if not has_newline:
                if at_blank_line:
                    curr_indent = curr_indent + last_indent
            else:
                curr_indent = last_indent
            return stmt.text

        elif isinstance(stmt, IfStatement):
            for (cond, cons) in stmt.cases:
                if eval_code_expr(cond, env):
                    env2 = env.fork()
                    return eval_statement_list(cons, env2)
            if stmt.alternative is not None:
                env2 = env.fork()
                return eval_statement_list(stmt.alternative, env2)
            return ''

        elif isinstance(stmt, ForInStatement):
            rng = eval_code_expr(stmt.expression, env)
            return eval_repeat(stmt.pattern, rng, stmt.body)

        elif isinstance(stmt, ExpressionStatement):
            return str(eval_code_expr(stmt.expression, env))

        elif isinstance(stmt, JoinStatement):
            rng = eval_code_expr(stmt.expression, env)
            sep = eval_code_expr(stmt.separator, env)
            return eval_repeat(stmt.pattern, rng, stmt.body, sep)

        else:
            raise TypeError("Could not evaluate statement: unknown statement {}.".format(stmt))

    env = Env()
    env.set('True', True)
    env.set('False', False)
    env.set('now', datetime.now().strftime("%b %d %Y %H:%M:%S"))
    for name, value in DEFAULT_BUILTINS.items():
        env.set(name, value)
    for name, value in ctx.items():
        env.set(name, value)
    return eval_statement_list(ast, env)

