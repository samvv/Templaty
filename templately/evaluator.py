
from textwrap import indent, dedent
import math

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
            break
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
            break
        i -= 1
    return text[0:i]

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
    return min_indent

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

def evaluate(ast, indentation='  '):

    indent_override = 0
    curr_indent = 0
    at_blank_line = True

    def eval_code_expr(e):
        if isinstance(e, ConstExpression):
            return e.value
        else:
            raise RuntimeError("Could not evaluate Templately expression.")

    def eval_statement_list(stmts, env):
        out = ''
        for stmt in stmts:
            result = eval_statement(stmt, env)
            if not isinstance(stmt, TextStatement):
                result = remove_last_newline(result)
            out += result
        return out

    def eval_statement(stmt, env):
        nonlocal curr_indent
        if isinstance(stmt, TextStatement):
            last_indent = 0
            has_newline = False
            for ch in reversed(stmt.text):
                if ch == ' ':
                    last_indent += 1
                elif ch == '\n':
                    has_newline = True
                    break
                else:
                    last_indent = 0
            if not has_newline:
                if at_blank_line:
                    curr_indent = curr_indent + last_indent
            else:
                curr_indent = last_indent
            return stmt.text
        elif isinstance(stmt, ForInStatement):
            #  strip_before = True
            if isinstance(stmt.expression, AppExpression) and stmt.expression.operator.name == 'range':
                low = eval_code_expr(stmt.expression.operands[0])
                high = eval_code_expr(stmt.expression.operands[1])
                env2 = env.fork()
                out = ''
                for i in range(low, high):
                    env2.set(stmt.pattern.name, i)
                    children = list(stmt.body)
                    strip_inner_before = len(children) > 0 and isinstance(children[0], TextStatement) and starts_with_newline(children[0].text)
                    #  strip_outer_after = len(children) > 0 and isinstance(children[-1], TextStatement) and ends_with_newline(children[-1].text)
                    smallest_indent = 0
                    for i, child in enumerate(children):
                        result = eval_statement(child, env2)
                        smallest_indent = min(smallest_indent, get_indentation(result))
                        if i == 0 and strip_inner_before: result = remove_first_newline(result)
                        out += result
                return indent(dedent(out), indentation * smallest_indent)
            else:
                raise RuntimeError("Unknown statement")
            #  strip_after = True
        elif isinstance(stmt, VarRefExpression):
            return str(env.lookup(stmt.name))

    env = Env()
    return eval_statement_list(ast, env)

