
from typing import Any, assert_never, cast
from sweetener import set_parent_nodes, warn
from datetime import datetime
from textwrap import indent, dedent

from .outline import outline
from .ast import *
from .util import is_blank, to_snake_case, to_camel_case

class OutputBase:

    def __init__(self) -> None:
        self.indent_override: str | None = None 

class TextOutput(OutputBase):

    def __init__(self, text = '') -> None:
        super().__init__()
        self.text = text

class BlockOutput(OutputBase):

    def __init__(self, children: list['Output'] | None = None) -> None:
        super().__init__()
        if children is None:
            children = []
        self.children = children

Output = TextOutput | BlockOutput

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


class Ref[T]:

    def __init__(self, value: T) -> None:
        self.value = value

shared_context = Ref[dict[str, Any]]({})

def load_context() -> dict[str, Any]:
    return shared_context.value

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
            low = expr.min and eval_expr(expr.min, env)
            high = expr.max and eval_expr(expr.max, env)
            return val[low:high]
        elif isinstance(expr, MemberExpression):
            out = eval_expr(expr.expression, env)
            for name in expr.members:
                out = getattr(out, name)
            return out
        elif isinstance(expr, VarRefExpression):
            assert(shared_context.value is not None)
            if expr.name in shared_context.value:
                return shared_context.value[expr.name]
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

    def align(text: str) -> str:
        if text.find('\n') != -1:
            text = indent(dedent(text), indentation * curr_indent)
        return text

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

    def eval_loop(stmt: ForInStatement | JoinStatement, env: Env, sep: Expression | None = None) -> Output:
        value = eval_expr(stmt.expression, env)
        out = BlockOutput()
        elements = list(value)
        for i, element in enumerate(elements):
            inner_env = Env(env)
            inner_env.set('index', i)
            bind_pattern(stmt.pattern, element, inner_env)
            result = eval_stmt(stmt.body, inner_env)
            out.children.append(result)
        # for i, res in enumerate(results):
        #     if sep_value and i < len(results)-1:
        #         k = rfind(res, lambda ch: not is_whitespace(ch))
        #         if k == -1:
        #             k = size(res)
        #         insert_after(res, k, wrap(str(sep_value)))
        #     out.extend(res)
        return out

    def eval_stmt(stmt: Node, env: Env) -> Output:

        if isinstance(stmt, Body):
            out = BlockOutput()
            def write(text):
                nonlocal out
                advance(text)
                out.children.append(TextOutput(text))
            env.set('write', write)
            for stmt in stmt.elements:
                result = eval_stmt(stmt, env)
                out.children.append(result)
            return out

        if isinstance(stmt, TextStatement):
            advance(stmt.text)
            return TextOutput(stmt.text)

        if isinstance(stmt, IfStatement):
            for case in stmt.cases:
                if case.test is None:
                    return eval_stmt(case.body, env)
                value = eval_expr(case.test, env)
                if value:
                    return eval_stmt(case.body, env)
            return TextOutput('')

        if isinstance(stmt, ForInStatement):
            return eval_loop(stmt, env)

        if isinstance(stmt, JoinStatement):
            return eval_loop(stmt, env, sep=stmt.separator)

        if isinstance(stmt, ExpressionStatement):
            value = eval_expr(stmt.expression, env)
            return TextOutput(align(str(value)))

        if isinstance(stmt, SetIndentStatement):
            level = eval_expr(stmt.level, env)
            result = eval_stmt(stmt.body, env)
            result.indent_override = indentation * level
            return result

        if isinstance(stmt, CodeBlock):
            globals = global_env.to_dict()
            locals = env.to_dict()
            exec(compile(stmt.module, filename=filename, mode='exec'), globals, locals)
            for k, v in locals.items():
                if k not in env or env.lookup(k) != v:
                    env.set(k, v)
            return TextOutput('')

        raise RuntimeError(f'unexpected node {stmt}')

    if isinstance(template, str):
        from .scanner import Scanner
        from .parser import Parser
        scanner = Scanner(filename, template)
        parser = Parser(scanner)
        template = parser.parse_all()
        set_parent_nodes(template)

    global_env = Env()
    global_env.update(DEFAULT_BUILTINS)
    global_env.update(ctx)
    global_env.set('now', datetime.now().strftime("%b %d %Y %H:%M:%S"))

    outline(template)

    output = eval_stmt(template.body, global_env)

    at_blank_line = True
    curr_indent = 0

    def get_indentation(output: Output, at_blank_line=True, default_indent=0, curr_indent=0) -> int:
        min_indent = None
        def visit(output: Output) -> None:
            nonlocal at_blank_line, curr_indent, min_indent
            if isinstance(output, TextOutput):
                for ch in output.text:
                    if at_blank_line:
                        if is_blank(ch):
                            curr_indent += 1
                            continue
                        if ch == '\n':
                            at_blank_line = False
                        elif min_indent is None or curr_indent < min_indent:
                            min_indent = curr_indent
                    else:
                        if ch == '\n':
                            at_blank_line = True
                            curr_indent = 0
                return
            if isinstance(output, BlockOutput):
                for child in output.children:
                    visit(child)
                return
            assert_never(output)
        visit(output)
        if min_indent is None:
            min_indent = default_indent if at_blank_line else curr_indent 
        return min_indent

    def render(output: Output, dedent_count: int | None, indentation: str | None) -> str:
        nonlocal at_blank_line, curr_indent
        if isinstance(output, TextOutput):
            out = ''
            for ch in output.text:
                if ch == '\n':
                    at_blank_line = True
                    curr_indent = 0
                    out += ch
                else:
                    if at_blank_line:
                        if is_blank(ch):
                            curr_indent += 1
                            if dedent_count is not None and curr_indent <= dedent_count:
                                continue
                        else:
                            if indentation is not None:
                                out += indentation
                            at_blank_line = False
                    out += ch
            return out
        if isinstance(output, BlockOutput):
            out = ''
            if output.indent_override:
                dedent_count = get_indentation(output, at_blank_line=at_blank_line, curr_indent=curr_indent)
                indentation = output.indent_override
            for child in output.children:
                out += render(child, dedent_count, indentation)
            return out
        assert_never(output)

    return render(output, None, None)

