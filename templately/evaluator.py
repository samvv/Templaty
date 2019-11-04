
from textwrap import indent, dedent

from .ast import *

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

class Context:

    def __init__(self, indentation='  ', indent_level=0):
        self.indentation = indentation
        self.indent_level = indent_level
        self.strip_newline_before = False
        self.strip_newline_after = False

    def clone(self):
        return Context(self.indentation, self.indent_level)

def evaluate(ast, out, indentation='  '):

    def eval_code_expr(e):
        if isinstance(e, ConstExpression):
            return e.value
        else:
            raise RuntimeError("Could not evaluate Templately expression.")

    def eval_statement(stmt, env, ctx):
        if isinstance(stmt, TextStatement):
            text = stmt.text
            if ctx.strip_newline_before:
                if len(text) > 2 and text[0] == '\r' and text[1] == '\n':
                    text = text[2:]
                elif len(text) > 1 and text[0] == '\n':
                    text = text[1:]
                ctx.strip_newline_before = False
            if ctx.strip_newline_after:
                if len(text) > 2 and text[-2] == '\r' and text[-1] == '\n':
                    text = text[0:-2]
                elif len(text) > 1 and text[-1] == '\n':
                    text = text[0:-1]
                ctx.strip_newline_after = False
            out.write(indent(dedent(text), ctx.indentation * ctx.indent_level))
        elif isinstance(stmt, ForInStatement):
            if isinstance(stmt.expression, AppExpression) and stmt.expression.operator.name == 'range':
                low = eval_code_expr(stmt.expression.operands[0])
                high = eval_code_expr(stmt.expression.operands[1])
                env2 = env.fork()
                ctx2 = ctx.clone()
                for i in range(low, high):
                    env2.set(stmt.pattern.name, i)
                    ctx2.strip_newline_before = True
                    for child in stmt.body:
                        eval_statement(child, env2, ctx2)
            else:
                raise RuntimeError("Unknown statement")
            ctx.strip_newline_after = True
        elif isinstance(stmt, VarRefExpression):
            out.write(str(env.lookup(stmt.name)))
    
    env = Env()
    ctx = Context()
    for stmt in ast:
        eval_statement(stmt, env, ctx)

