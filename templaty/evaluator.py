
from textwrap import indent, dedent
from datetime import datetime
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

class Builtin:
    pass

class FunctionBuiltin(Builtin):
    pass

class VariableBuiltin(Builtin):
    pass

def func(builtin_name):
    def decorate(f):
        class MyBuiltin(FunctionBuiltin):
            name = builtin_name
            def apply(self, args):
                return f(*args)
    return decorate

def getter(builtin_name):
    def decorate(f):
        class MyBuilting(VariableBuiltin):
            name = builtin_name
            def get(self):
                return f()

def has_class_property(cls, name):
    try:
        cls.name
        return True
    except AttributeError:
        return False

EXCLUDE_BUILTINS = [FunctionBuiltin, VariableBuiltin]

def get_all_builtins():
    to_visit = [Builtin]
    while len(to_visit) > 0:
        my_class = to_visit.pop()
        if hasattr(my_class, 'name'):
            yield my_class
        for builtin_class in my_class.__subclasses__():
            to_visit.append(builtin_class)

def evaluate(ast, data={}, indentation='  '):

    indent_override = 0
    curr_indent = 0
    at_blank_line = True

    def eval_code_expr(e, env):
        if isinstance(e, ConstExpression):
            return e.value
        elif isinstance(e, VarRefExpression):
            value = env.lookup(e.name)
            if isinstance(value, VariableBuiltin):
                return value.get()
            else:
                return value
        elif isinstance(e, AppExpression):
            op = eval_code_expr(e.operator, env)
            args = list(eval_code_expr(arg, env) for arg in e.operands)
            if not isinstance(op, FunctionBuiltin):
                raise RuntimeError("Could not evaluate Templately expression: result is not applicable.".format(op))
            return op.apply(args)
        else:
            raise RuntimeError("Could not evaluate Templately expression: unknown expression {}.".format(e))

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
            env2 = env.fork()
            out = ''
            for i in rng:
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

        elif isinstance(stmt, ExpressionStatement):
            return str(eval_code_expr(stmt.expression, env))

        elif isinstance(stmt, JoinStatement):
            rng = eval_code_expr(stmt.expression, env)
            sep = eval_code_expr(stmt.separator, env)
            env2 = env.fork()
            out = ''
            for i in rng:
                if i > 0: out += sep
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
            raise TypeError("Could not evaluate statement: unknown statement {}.".format(stmt))

    env = Env()
    for builtin_class in get_all_builtins():
        env.set(builtin_class.name, builtin_class())
    for name, value in data.items():
        env.set(name, value)
    return eval_statement_list(ast, env)

