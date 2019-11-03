
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

def evaluate(ast, out, env=Env()):

    def eval_expr(e):
        if isinstance(e, ConstExpression):
            return e.value
        else:
            raise RuntimeError("Could not evaluate Templately expression.")

    for stmt in ast:
        if isinstance(stmt, TextStatement):
            out.write(stmt.text)
        elif isinstance(stmt, ForInStatement):
            if isinstance(stmt.expression, AppExpression) and stmt.expression.operator.name == 'range':
                low = eval_expr(stmt.expression.operands[0])
                high = eval_expr(stmt.expression.operands[1])
                env2 = env.fork()
                for i in range(low, high):
                    env2.set(stmt.pattern.name, i)
                    evaluate(stmt.body, out, env2)
        elif isinstance(stmt, VarRefExpression):
            out.write(str(env.lookup(stmt.name)))

