
from datetime import datetime
import textwrap
import ast

from .scanner import Position
from .ast import *
from .util import get_indentation, preorder, is_blank, starts_with_newline, ends_with_newline, remove_first_newline

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

#  def remove_first_indentation(text):
#      i = 0
#      while i < len(text):
#          if not is_blank(text[i]):
#              break
#          i += 1
#      return text[i:]

def is_inner_wrapped(stmt):
    return len(stmt.body) > 0 \
       and isinstance(stmt.body[0], TextStatement) \
       and starts_with_newline(stmt.body[0].text) \
       and isinstance(stmt.body[-1], TextStatement) \
       and ends_with_newline(stmt.body[-1].text)

def is_after_blank_line(node):
    prev_node = node.get_prev_node(TextStatement)
    if prev_node is not None:
        for ch in reversed(prev_node.text):
            if ch == '\n':
                return True
            if not is_blank(ch):
                break
    return False

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
                min_indent = 0
            return min_indent
        else:
            at_blank_line = False

    #  at_blank_line = is_after_blank_line(node)
    #  def visit(node):
    #      if isinstance(node, TextStatement):
    #          return get_indentation(node.text, at_blank_line=at_blank_line)
    #      elif isinstance(node, ForInStatement):
    #          min_indent = None
    #          for stmt in node.body:
    #              stmt_indent = visit(stmt)
    #              if stmt_indent is not None:
    #                  if min_indent is None or stmt_indent < min_indent:
    #                      min_indent = stmt_indent
    #          if min_indent is None:
    #              min_indent = 0
    #          return min_indent
    #      else:
    #          raise RuntimeError("Could not get indentation of node {}".format(node))
    #  return visit(node)

def evaluate(ast, ctx={}, indentation='  ', filename="#<anonymous>"):

    if isinstance(ast, str):
        from .scanner import Scanner
        from .parser import Parser
        sc = Scanner(filename, ast)
        p = Parser(sc)
        ast = p.parse_all()
        #  for node in ast:
        #      set_all_parents(node)

    curr_indent = ''
    at_blank_line = True
    strip_next_newline = False

    #  def count_newlines(lines):
    #      count = 0
    #      join_with_prev = False
    #      for line in lines:
    #          if not line.join_previous and not join_with_prev:
    #              count += 1
    #          join_with_prev = line.join_next
    #      return count

    #  def get_indentation(text):
    #      out = ''
    #      for ch in text:
    #          if ch == ' ' or ch == '\t':
    #              out += ch
    #          else:
    #              break
    #      return out

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
            out += eval_statement(stmt, env)
        return out

    def indent_depth(indentation):
        return len(indentation)

    def get_indentation_of_last_line(text):
        nonlocal at_blank_line
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
                return curr_indent + last_indent
            else:
                return curr_indent
        else:
            return last_indent

    def eval_repeat(stmt, sep, env):
        out = ''
        rng = eval_code_expr(stmt.expression, env)
        count = max(rng) - min(rng) + 1
        env2 = env.fork()
        outer_indent = len(curr_indent)
        inner_indent = get_inner_indentation(stmt, at_blank_line)
        wrapped = is_inner_wrapped(stmt)
        for i in range(0, count):
            if i > 0: out += sep
            env2.set(stmt.pattern.name, i + min(rng))
            for j, child in enumerate(stmt.body):
                result = eval_statement(child, env2)
                if i == 0 and j == 0 and wrapped:
                    result = ' ' * inner_indent + result[inner_indent+1:]
                if j == len(stmt.body) - 1 and wrapped:
                    result = result[:-(outer_indent+1)]
                out += result
        if wrapped:
            out = textwrap.indent(textwrap.dedent(out), ' ' * outer_indent)
        else:
            out = textwrap.indent(out, ' ' * outer_indent)
        out = out[outer_indent:]
        return out

    def eval_statement(stmt, env):

        nonlocal curr_indent, at_blank_line, strip_next_newline

        strip_curr_newline = strip_next_newline
        strip_next_newline = False

        if isinstance(stmt, TextStatement):
            curr_indent = get_indentation_of_last_line(stmt.text)
            text = stmt.text
            if strip_curr_newline:
                text = remove_first_newline(text)
            return text

        elif isinstance(stmt, IfStatement):
            for (cond, cons) in stmt.cases:
                if eval_code_expr(cond, env):
                    env2 = env.fork()
                    return eval_statement_list(cons, env2)
            if stmt.alternative is not None:
                env2 = env.fork()
                return eval_statement_list(stmt.alternative, env2)
            return ''

        elif isinstance(stmt, CodeBlock):
            exec(compile(stmt.module, filename=filename, mode='exec'), global_env._variables, env._variables)
            strip_next_newline = True
            return ''

        #  elif isinstance(stmt, NoIndentStatement):

        #      lines = eval_statement_list(stmt.body, env)
        #      dedent(lines)
        #      override_indent(lines, 0)
        #      wrapped = is_inner_wrapped(stmt.body)
        #      if wrapped and len(lines) > 0:
        #          lines[0].join_previous = True
        #      if wrapped and len(lines) > 0:
        #          lines[-1].join_previous = True
        #      return lines

        elif isinstance(stmt, ExpressionStatement):
            return str(eval_code_expr(stmt.expression, env))

        elif isinstance(stmt, ForInStatement):
            return eval_repeat(stmt, '', env)

        elif isinstance(stmt, JoinStatement):
            sep = str(eval_code_expr(stmt.separator, env))
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

    return eval_statement_list(ast, global_env)

