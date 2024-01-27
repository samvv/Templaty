
import sys

from .ast import *

def emit(node: Node, out = sys.stdout) -> None:

    def visit(node: Node) -> None:

        if isinstance(node, Body):
            for element in node.elements:
                visit(element)
            return

        if isinstance(node, ExpressionStatement):
            out.write('{{')
            visit(node.expression)
            out.write('}}')
            return

        if isinstance(node, IfStatement):
            out.write('{% if ')
            assert(node.cases[0].test is not None)
            visit(node.cases[0].test)
            out.write(' %}')
            visit(node.cases[0].body)
            for case in node.cases[1:]:
                if case.test is None:
                    out.write('{% else %}')
                else:
                    out.write('{% elif ')
                    visit(case.test)
                    out.write(' %}')
                visit(case.body)
            out.write('{% endif %}')
            return

        if isinstance(node, JoinStatement):
            out.write('{% join ')
            visit(node.pattern)
            out.write(' in ')
            visit(node.expression)
            out.write(' with ')
            visit(node.separator)
            out.write(' %}')
            visit(node.body)
            out.write('{% endfor %}')
            return

        if isinstance(node, ForInStatement):
            out.write('{% for ')
            visit(node.pattern)
            out.write('  in ')
            visit(node.expression)
            out.write(' %}')
            visit(node.body)
            out.write('{% endfor %}')
            return

        if isinstance(node, TextStatement):
            out.write(node.text)
            return

        if isinstance(node, VarPattern):
            out.write(node.name)
            return

        if isinstance(node, VarRefExpression):
            out.write(node.name)
            return

        if isinstance(node, ConstExpression):
            out.write(repr(node.value))
            return

        if isinstance(node, Template):
            visit(node.body)
            return

        if isinstance(node, CallExpression):
            visit(node.operator)
            out.write('(')
            first = True
            for arg in node.operands:
                if not first:
                    out.write(', ')
                visit(arg)
                first = False
            out.write(')')
            return

        raise RuntimeError(f'unexpected {node}')

    visit(node)

