
import math
from typing import Callable, TypeGuard, TypeVar, cast
from functools import cache

from .emitter import emit
from .util import is_blank
from .ast import *

tab_size = 4

def count_spaces(ch: str) -> int:
    if ch == ' ':
        return 1
    if ch == '\t':
        return tab_size
    raise NotImplementedError()

type NodeWithBody = Template | ForInStatement | JoinStatement | SetIndentStatement

type BlockNode = ForInStatement | JoinStatement | SetIndentStatement | CodeBlock

@cache
def get_indent(node: Node, at_blank_line = True, curr_indent = 0) -> int | None:

    min_indent = math.inf

    def visit(node: Node) -> None:

        nonlocal at_blank_line, curr_indent, min_indent

        if isinstance(node, TextStatement):
            for ch in node.text:
                if ch == '\n':
                    at_blank_line = True
                    curr_indent = 0
                elif at_blank_line:
                    if is_blank(ch):
                        curr_indent += 1
                    else:
                        at_blank_line = False
                        if curr_indent < min_indent:
                            min_indent = curr_indent
            return

        if isinstance(node, IfStatement):
            for case in node.cases:
                visit(case)
            return

        if isinstance(node, IfStatementCase) \
                or isinstance(node, ForInStatement) \
                or isinstance(node, JoinStatement) \
                or isinstance(node, SetIndentStatement):
            at_blank_line = False
            if curr_indent < min_indent:
                min_indent = curr_indent
            visit(node.body)
            return

        if isinstance(node, ExpressionStatement) \
            or isinstance(node, CodeBlock):
            at_blank_line = False
            if curr_indent < min_indent:
                min_indent = curr_indent
            return

        if isinstance(node, Body):
            for element in node.elements:
                visit(element)
            return

        if isinstance(node, Template):
            visit(node.body)
            return

        raise RuntimeError(f'unexpected {node}')

    visit(node)

    if isinstance(min_indent, float):
        if at_blank_line:
            return None
        return curr_indent
    return min_indent

def dedent(node: Node, indent_level: int | None = None, outer_indent = 0, at_blank_line = True, curr_indent = 0) -> None :

    def visit(node: Node, indent_level: int, is_last: bool) -> None:
        nonlocal at_blank_line, curr_indent
        if isinstance(node, ExpressionStatement) \
            or isinstance(node, CodeBlock):
            at_blank_line = False
            return
        if isinstance(node, TextStatement):
            new_text = ''
            for ch in node.text:
                if ch == '\n':
                    at_blank_line = True
                    curr_indent = 0
                elif at_blank_line:
                    if is_blank(ch):
                        if curr_indent >= indent_level:
                            new_text += ch
                        # FIXME if count_spaces(ch) > 1 this gives issues
                        curr_indent += count_spaces(ch)
                        continue # do not append ch
                    else:
                        at_blank_line = False
                new_text += ch
            if is_last and at_blank_line:
                remaining = max(0, curr_indent - indent_level)
                new_text += ' ' * (outer_indent - remaining)
            node.text = new_text
            return
        if isinstance(node, Body):
            for i, element in enumerate(node.elements):
                visit(element, indent_level, is_last and i == len(node.elements)-1)
            return
        if isinstance(node, IfStatement):
            for i, case in enumerate(node.cases):
                visit(case, indent_level, is_last and i == len(node.cases)-1)
            return
        if isinstance(node, IfStatementCase) \
            or isinstance(node, ForInStatement) \
                or isinstance(node, JoinStatement) \
                or isinstance(node, SetIndentStatement):
            at_blank_line = False
            visit(node.body, indent_level, is_last)
            return
        raise RuntimeError(f'unexpected {node}')

    if indent_level is None:
        indent_level = get_indent(node)
        if indent_level is None:
            indent_level = 0
    visit(node, indent_level, True)

# def indent(node: Body, indentation: str, at_blank_line = True) -> None:
#
#     def visit(node: Node) -> None:
#         nonlocal at_blank_line
#         if isinstance(node, TextStatement):
#             new_text = ''
#             for ch in node.text:
#                 if ch == '\n':
#                     at_blank_line = True
#                 elif at_blank_line and not is_blank(ch):
#                     new_text += indentation
#                     at_blank_line = False
#                 new_text += ch
#             node.text = new_text
#             return
#         if isinstance(node, ForInStatement) \
#                 or isinstance(node, JoinStatement) \
#                 or isinstance(node, SetIndentStatement):
#             if at_blank_line:
#                 node.insert_before(TextStatement(indentation))
#                 at_blank_line = False
#             return
#         raise RuntimeError(f'unexpected {node}')
#
#     visit(node)

def assign_indent_levels(template: Template) -> None:

    curr_indent = 0
    at_blank_line = True

    def visit(node: Node) -> None:

        nonlocal curr_indent, at_blank_line

        node.indent_level = curr_indent

        if isinstance(node, TextStatement):
            for ch in node.text:
                if ch == '\n':
                    at_blank_line = True
                    curr_indent = 0
                elif at_blank_line:
                    if is_blank(ch):
                        curr_indent += 1
                    else:
                        at_blank_line = False
            return


        if isinstance(node, Body):
            for element in node.elements:
                visit(element)
            return

        if isinstance(node, IfStatement):
            for case in node.cases:
                visit(case)
            return

        if isinstance(node, ExpressionStatement) \
            or isinstance(node, CodeBlock):
            at_blank_line = False
            return

        if isinstance(node, Template) \
            or isinstance(node, IfStatementCase) \
            or isinstance(node, ForInStatement) \
            or isinstance(node, JoinStatement) \
            or isinstance(node, SetIndentStatement):
            #inner_indent = get_indent(node.body, at_blank_line, curr_indent)
            visit(node.body)
            return

        raise RuntimeError(f'unexpected {node}')
 
    visit(template)

def remove_left_while(node: BaseNode | None, pred: Callable[[str], bool]) -> None:
    while True:
        if node is None:
            break
        if not isinstance(node, TextStatement):
            break
        i = len(node.text)
        while i > 0 and pred(node.text[i-1]):
            i -= 1
        node.text = node.text[0:i]
        if i > 0:
            break
        node = node.prev_sibling

def remove_right_while(node: BaseNode | None, pred: Callable[[str], bool]) -> None:
    while True:
        if node is None:
            break
        if not isinstance(node, TextStatement):
            break
        i = 0
        while i < len(node.text) and pred(node.text[i]):
            i += 1
        node.text = node.text[i:]
        if i < len(node.text):
            break
        node = node.prev_sibling

def single_newline():
    found_newline = False
    def pred(ch):
        nonlocal found_newline
        if found_newline:
            return False
        if is_blank(ch):
            return True
        if ch == '\n':
            found_newline = True
            return True
        return False
    return pred

def has_newline_or_eof_right(node: BaseNode | None):
    while True:
        if node is None:
            return True
        if not isinstance(node, TextStatement):
            return False
        for ch in node.text:
            if ch == '\n':
                return True
            elif not is_blank(ch):
                return False
        node = node.next_sibling

def has_newline_or_eof_left(node: BaseNode | None):
    while True:
        if node is None:
            return True
        if not isinstance(node, TextStatement):
            return False
        for ch in reversed(node.text):
            if ch == '\n':
                return True
            elif not is_blank(ch):
                return False
        node = node.prev_sibling

def has_body(node: Node) -> TypeGuard[NodeWithBody]:
        return isinstance(node, Template) \
            or isinstance(node, ForInStatement) \
            or isinstance(node, JoinStatement) \
            or isinstance(node, SetIndentStatement)

def can_be_block(node: Node) -> TypeGuard[BlockNode]:
    return isinstance(node, CodeBlock) or has_body(node)

@cache
def is_block(stmt: Statement) -> bool:
    if isinstance(stmt, CodeBlock) or isinstance(stmt, CommentStatement):
        return has_newline_or_eof_left(stmt.prev_sibling) \
            and has_newline_or_eof_right(stmt.next_sibling)
    if has_body(stmt):
        return has_newline_or_eof_left(stmt.prev_sibling) \
            and has_newline_or_eof_right(stmt.next_sibling) \
            and has_newline_or_eof_right(stmt.body.first_child) \
            and has_newline_or_eof_left(stmt.body.last_child)
    return False


def outline(template: Template) -> None:

    def remove_comments(node: Node) -> None:
        if isinstance(node, CommentStatement):
            if is_block(node):
                remove_right_while(node.next_sibling, single_newline())
            node.remove()
            return
        if isinstance(node, Body):
            for element in node.elements:
                remove_comments(element)
            return
        if has_body(node):
            remove_comments(node.body)
            return

    def redent_blocks(node: Node) -> None:
        if isinstance(node, TextStatement) \
            or isinstance(node, ExpressionStatement) \
            or isinstance(node, CodeBlock):
            return
        if isinstance(node, Body):
            for stmt in node.elements:
                redent_blocks(stmt)
            if node.parent is not None and is_block(node.parent):
                outer_indent = cast(Node, node.parent).indent_level
                inner_indent = get_indent(node)
                if outer_indent is not None and inner_indent is not None:
                    #keep = get_last_blank_line(node.last_child)
                    dedent(node, inner_indent - outer_indent, outer_indent)
                    #node.last_child.text = node.last_child.text + keep
            return
        if isinstance(node, IfStatement):
            for case in node.cases:
                redent_blocks(case.body)
            return
        if isinstance(node, Template) \
                or isinstance(node, ForInStatement) \
                or isinstance(node, JoinStatement) \
                or isinstance(node, SetIndentStatement):
            redent_blocks(node.body)
            return
        raise RuntimeError(f'unexpected {node}')

    def undent_specials(node: BaseNode | None) -> None:
        if node is None:
            return
        if isinstance(node, Body):
            for element in node.elements:
                undent_specials(element)
            return
        if isinstance(node, CodeBlock):
            remove_left_while(node.prev_sibling, is_blank)
            return
        if isinstance(node, TextStatement) \
            or isinstance(node, ExpressionStatement):
            return
        if isinstance(node, IfStatement):
            if is_block(node):
                remove_left_while(node.prev_sibling, is_blank)
            for case in node.cases:
                undent_specials(case)
            return
        if isinstance(node, IfStatementCase):
            if is_block(node.parent):
                remove_left_while(node.body.last_child, is_blank)
            return
        if isinstance(node, ForInStatement) \
            or isinstance(node, JoinStatement) \
            or isinstance(node, SetIndentStatement):
            if is_block(node) and node.prev_sibling is not None:
                remove_left_while(node.prev_sibling, is_blank)
                remove_left_while(node.body.last_child, is_blank)
            undent_specials(node.body)
            return
        raise RuntimeError(f'unexpected {node}')

    def remove_block_newlines(node: Node) -> None:

        if isinstance(node, Body):
            for element in node.elements:
                remove_block_newlines(element)

        elif has_body(node):
            remove_block_newlines(node.body)

        if not is_block(node):
            return

        if isinstance(node, CodeBlock):
            remove_right_while(node.next_sibling, single_newline())
            return

        if has_body(node):
            remove_right_while(node.body.first_child, single_newline())
            remove_right_while(node.next_sibling, single_newline())
            return

        raise RuntimeError(f'unexpected {node}')

    remove_comments(template)
    assign_indent_levels(template)
    redent_blocks(template.body)
    undent_specials(template.body);
    remove_block_newlines(template.body)

