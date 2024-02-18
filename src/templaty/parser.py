
import textwrap
import ast
import heapq
from typing import Never
from sweetener import TextFile, clone

from .scanner import *
from .ast import *
from .util import *

PRECEDENCE_TABLE = [
    (2, OR_OPERATOR, 0),
    (2, AND_OPERATOR, 1),
    (1, NOT_OPERATOR, 2),
    (2, IN_KEYWORD, 3),
    (2, LT_OPERATOR, 3),
    (2, LTE_OPERATOR, 3),
    (2, GT_OPERATOR, 3), 
    (2, GTE_OPERATOR, 3), 
    (2, NEQ_OPERATOR, 3),
    (2, EQ_OPERATOR, 3),
    (2, BOR_OPERATOR, 4),
    (2, BAND_OPERATOR, 5),
    (2, LSHIFT_OPERATOR, 6),
    (2, RSHIFT_OPERATOR, 6),
    (2, ADD_OPERATOR, 7),
    (2, SUB_OPERATOR, 7),
    (2, MUL_OPERATOR, 8),
    (2, DIV_OPERATOR, 8),
    (1, AT, 8),
    (2, REM_OPERATOR, 8),
    (2, MOD_OPERATOR, 8),
    (1, SUB_OPERATOR, 9),
    (1, ADD_OPERATOR, 9),
    (1, BNOT_OPERATOR, 9),
    (2, EXP_OPERATOR, 10),
    (2, PIPE_OPERATOR, 11)
    ]

def is_right_assoc(name: str) -> bool:
    return name == '**'

def is_operator(token_type: TokenType, arity: int) -> bool:
    for (arity_2, token_type_2, prec) in PRECEDENCE_TABLE:
        if token_type_2 == token_type and arity_2 == arity:
            return True
    return False

def get_operator_precedence(token_type: TokenType, arity: int) -> int | None:
    try:
        return next(prec for (arity_2, token_type_2, prec) in PRECEDENCE_TABLE if token_type == token_type_2 and arity == arity_2)
    except StopIteration:
        return None

#  def get_end_token_type(tt):
#      if tt == JOIN_KEYWORD:
#          return ENDJOIN_KEYWORD
#      elif tt == FOR_KEYWORD:
#          return ENDFOR_KEYWORD

class ParseError(RuntimeError):

    def __init__(self, filename: str, start_pos: TextPos, end_pos: TextPos, expected: list[TokenType], actual: Token):
        expected_str = enum_or(token_type_to_string(tt) for tt in expected)
        super().__init__(f"{filename}:{start_pos.line}:{start_pos.column}: Expected {expected_str} but got '{actual.text}'")
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.expected = expected
        self.actual = actual

class Parser:

    def __init__(self, scanner: Scanner) -> None:
        self.scanner = scanner
        self.file = scanner.file
        self._token_stream = scanner.scan()
        self._token_buffer = []
        self._statement_stack = []

    def peek_token(self, count=1) -> Token:
        while len(self._token_buffer) < count:
            t0 = next(self._token_stream)
            self._token_buffer.append(t0)
        return self._token_buffer[count-1]

    def get_token(self) -> Token:
        if len(self._token_buffer) > 0:
            return self._token_buffer.pop(0)
        return next(self._token_stream)

    def expect_token(self, token_type) -> None:
        token = self.get_token()
        if token.type != token_type:
            self._raise_parse_error(token, [token_type])

    def parse_tuple_pattern_element(self) -> Pattern:
        t0 = self.get_token()
        if t0.type == OPEN_PAREN:
            self.get_token()
            nested = self.parse_pattern()
            self.expect_token(CLOSE_PAREN)
            return nested
        if t0.type != IDENTIFIER:
            self._raise_parse_error(t0, [IDENTIFIER])
        return VarPattern(t0.value)

    def parse_pattern(self):
        elements = [ self.parse_tuple_pattern_element() ]
        while True:
            t1 = self.peek_token()
            if t1.type != COMMA:
                break
            self.get_token()
            elements.append(self.parse_tuple_pattern_element())
        if len(elements) == 1:
            return elements[0]
        return TuplePattern(elements)

    def parse_member_expression(self, expr: Expression) -> Expression:
        self._expect_token(DOT)
        t0 = self.get_token()
        if t0.type != IDENTIFIER:
            self._raise_parse_error(t0, [IDENTIFIER])
        if isinstance(expr, MemberExpression):
            expr.members.append(t0.value)
        else:
            expr = MemberExpression(expr, [t0.value])
        return expr

    def parse_func_args(self) -> Generator[Expression, None, None]:
        first = True
        while True:
            t0 = self.peek_token()
            if t0.type == END_OF_FILE:
                self._raise_parse_error(t0, [CLOSE_PAREN])
            elif t0.type == CLOSE_PAREN:
                break
            else:
                if not first:
                    if t0.type != COMMA:
                        self._raise_parse_error(t0, [COMMA])
                    self.get_token()
                else:
                    first = False
                yield self.parse_expression()

    def parse_app_expression(self, expr: Expression) -> CallExpression:
        self._expect_token(OPEN_PAREN)
        args = list(self.parse_func_args())
        self._expect_token(CLOSE_PAREN)
        return CallExpression(expr, args)

    def parse_slice_expression(self, expr: Expression) -> Expression:
        self._expect_token(OPEN_BRACKET)
        t0 = self.peek_token()
        if t0.type == COLON:
            e1 = None
        else:
            e1 = self.parse_expression()
        t1 = self.get_token()
        if t1.type == CLOSE_BRACKET:
            assert(e1 is not None)
            return IndexExpression(expr, e1)
        elif t1.type == COLON:
            t2 = self.peek_token()
            if t2.type == CLOSE_BRACKET:
                e2 = None
            else:
                e2 = self.parse_expression()
            self._expect_token(CLOSE_BRACKET)
            return SliceExpression(expr, e1, e2)
        else:
            self._raise_parse_error(t1, [COLON, CLOSE_BRACKET])

    def parse_chained_expression(self) -> Expression:
        expr = self.parse_prim_expression()
        while True:
            t1 = self.peek_token()
            if t1.type == DOT:
                expr = self.parse_member_expression(expr)
            elif t1.type == OPEN_PAREN:
                expr = self.parse_app_expression(expr)
            elif t1.type == OPEN_BRACKET:
                expr = self.parse_slice_expression(expr)
            else:
                break
        return expr

    def parse_unary_expression(self) -> Expression:
        heap = []
        while True:
            t0 = self.peek_token()
            if is_operator(t0.type, 1):
                self.get_token()
                t0_prec = get_operator_precedence(t0.type, 1)
                heapq.heappush(heap, (t0_prec, t0))
            else:
                break
        e = self.parse_chained_expression()
        while len(heap) > 0:
            e = CallExpression(VarRefExpression(heapq.heappop(heap)[1].value), [e])
        return e

    def parse_prim_expression(self) -> Expression:
        t0 = self.get_token()
        if t0.type == OPEN_PAREN:
            e = self.parse_tuple_expression()
            self._expect_token(CLOSE_PAREN)
            return e
        elif t0.type == STRING_LITERAL:
            return ConstExpression(t0.value, span=t0.span)
        elif t0.type == INTEGER:
            return ConstExpression(t0.value, span=t0.span)
        elif t0.type == IDENTIFIER:
            return VarRefExpression(t0.value, span=t0.span)
        else:
            self._raise_parse_error(t0, [IDENTIFIER, STRING_LITERAL, INTEGER, OPEN_PAREN])

    def parse_binary_operators(self, lhs: Expression, min_prec: int) -> Expression:
        t0 = self.peek_token()
        while True:
            if not is_operator(t0.type, 2):
                break
            keep = t0
            keep_prec = get_operator_precedence(keep.type, 2)
            if keep_prec is None or keep_prec < min_prec:
                break
            self.get_token()
            rhs = self.parse_unary_expression()
            t0 = self.peek_token()
            while True:
                if not is_operator(t0.type, 2):
                    break
                t0_prec = get_operator_precedence(t0.type, 2)
                if not (t0_prec is not None and (t0_prec > keep_prec or (is_right_assoc(t0.value) and t0_prec == keep_prec))):
                    break
                rhs = self.parse_binary_operators(rhs, t0_prec)
                t0 = self.peek_token()
            lhs = CallExpression(VarRefExpression(keep.value), [lhs, rhs])
        return lhs

    def parse_expression(self):
        return self.parse_binary_operators(self.parse_unary_expression(), 0)

    def parse_tuple_expression(self):
        exps = [ self.parse_expression() ]
        while True:
            t1 = self.peek_token()
            if t1.type != COMMA:
                break
            self.get_token()
            exps.append(self.parse_expression())
        if len(exps) == 1:
            return exps[0]
        return TupleExpression(exps)

    def parse_expression_statement(self) -> ExpressionStatement:
        t0 = self._expect_token(OPEN_EXPRESSION_BLOCK)
        e = self.parse_expression()
        t2 = self._expect_token(CLOSE_EXPRESSION_BLOCK)
        return ExpressionStatement(e, span=TextSpan(self.file, clone(t0.span.start_pos), clone(t2.span.end_pos)))

    def _raise_parse_error(self, token, expected) -> Never:
        raise ParseError(self.scanner.get_filename(), token.span.start_pos, token.span.end_pos, expected, token)

    def _get_text(self, token) -> str:
        return token.get_text(self.scanner._data)

    def _expect_token(self, tt) -> Token:
        t0 = self.get_token()
        if t0.type != tt:
            self._raise_parse_error(t0, [tt])
        return t0

    def parse_statement(self) -> Statement:
        t0 = self._expect_token(OPEN_STATEMENT_BLOCK)
        t1 = self.get_token()
        if t1.type == IF_KEYWORD:
            self._statement_stack.append([ENDIF_KEYWORD, ELIF_KEYWORD, ELSE_KEYWORD])
            cond = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            then = list(self.parse_statement_block())
            last_token = self.peek_token()
            cases = [IfStatementCase(cond, then, span=TextSpan(self.file, clone(t0.span.start_pos), clone(last_token.span.end_pos)))]
            while True:
                first_token = self._expect_token(OPEN_STATEMENT_BLOCK)
                t2 = self.get_token()
                if t2.type == ELIF_KEYWORD:
                    cond = self.parse_expression()
                    self._expect_token(CLOSE_STATEMENT_BLOCK)
                    then = list(self.parse_statement_block())
                    last_token = self.peek_token()
                    cases.append(IfStatementCase(cond, then, span=TextSpan(self.file, clone(first_token.span.start_pos), clone(last_token.span.end_pos))))
                elif t2.type == ELSE_KEYWORD:
                    self._expect_token(CLOSE_STATEMENT_BLOCK)
                    self._statement_stack[-1] = [ENDIF_KEYWORD]
                    body = Body(list(self.parse_statement_block()))
                    self._expect_token(OPEN_STATEMENT_BLOCK)
                    self._expect_token(ENDIF_KEYWORD)
                    last_token = self._expect_token(CLOSE_STATEMENT_BLOCK)
                    cases.append(IfStatementCase(None, body, span=TextSpan(self.file, clone(first_token.span.start_pos), clone(last_token.span.end_pos))))
                    break
                elif t2.type == ENDIF_KEYWORD:
                    last_token = self._expect_token(CLOSE_STATEMENT_BLOCK)
                    break
            return IfStatement(cases, span=TextSpan(self.file, clone(t0.span.start_pos), clone(last_token.span.end_pos)))
        elif t1.type == FOR_KEYWORD:
            self._statement_stack.append([ENDFOR_KEYWORD])
            patt = self.parse_pattern()
            self._expect_token(IN_KEYWORD)
            e = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = Body(list(self.parse_statement_block()))
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDFOR_KEYWORD)
            t7 = self._expect_token(CLOSE_STATEMENT_BLOCK)
            return ForInStatement(patt, e, body, span=TextSpan(self.file, clone(t0.span.start_pos), clone(t7.span.end_pos)))
        elif t1.type == JOIN_KEYWORD:
            self._statement_stack.append([ENDJOIN_KEYWORD])
            patt = self.parse_pattern()
            self._expect_token(IN_KEYWORD)
            e = self.parse_expression()
            self._expect_token(WITH_KEYWORD)
            sep = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = Body(list(self.parse_statement_block()))
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDJOIN_KEYWORD)
            t6 = self._expect_token(CLOSE_STATEMENT_BLOCK)
            return JoinStatement(patt, e, sep, body, span=TextSpan(self.file, clone(t0.span.start_pos), clone(t6.span.end_pos)))
        elif t1.type == SETINDENT_KEYWORD:
            self._statement_stack.append([ENDSETINDENT_KEYWORD])
            e = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = Body(list(self.parse_statement_block()))
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDSETINDENT_KEYWORD)
            t5 = self._expect_token(CLOSE_STATEMENT_BLOCK)
            return SetIndentStatement(e, body, span=TextSpan(self.file, clone(t0.span.start_pos), clone(t5.span.end_pos)))
        elif t1.type == NOINDENT_KEYWORD:
            self._statement_stack.append([ENDNOINDENT_KEYWORD])
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = Body(list(self.parse_statement_block()))
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDNOINDENT_KEYWORD)
            t5 = self._expect_token(CLOSE_STATEMENT_BLOCK)
            return SetIndentStatement(ConstExpression(0), body, span=TextSpan(self.file, clone(t0.span.start_pos), clone(t5.span.end_pos)))
        else:
            expected = [FOR_KEYWORD, JOIN_KEYWORD, IF_KEYWORD, NOINDENT_KEYWORD, SETINDENT_KEYWORD]
            if len(self._statement_stack) > 0:
                expected.extend(self._statement_stack[-1])
            self._raise_parse_error(t1, expected)

    def parse_statement_block(self) -> Generator[Statement, None, None]:
        close_tts = self._statement_stack[-1]
        while True:
            t0 = self.peek_token(1)
            t1 = self.peek_token(2)
            if t0.type == OPEN_STATEMENT_BLOCK and t1.type in close_tts:
                break
            else:
                yield self.parse()

    def parse_code_block(self) -> CodeBlock:
        self._expect_token(OPEN_CODE_BLOCK)
        t0 = self.get_token()
        if t0.type != CODE_BLOCK_CONTENT:
            self._raise_parse_error(t0, [CODE_BLOCK_CONTENT])
        module = ast.parse(textwrap.dedent(t0.value))
        self._expect_token(CLOSE_CODE_BLOCK)
        return CodeBlock(module)

    def parse(self) -> Statement:
        t0 = self.peek_token()
        if t0.type == TEXT:
            self.get_token()
            return TextStatement(t0.value, span=t0.span)
        elif t0.type == COMMENT:
            self.get_token()
            return CommentStatement(t0.value, span=t0.span)
        elif t0.type == OPEN_CODE_BLOCK:
            return self.parse_code_block()
        elif t0.type == OPEN_EXPRESSION_BLOCK:
            return self.parse_expression_statement()
        elif t0.type == OPEN_STATEMENT_BLOCK:
            return self.parse_statement()
        else:
            self._raise_parse_error(t0, [TEXT, OPEN_EXPRESSION_BLOCK, OPEN_STATEMENT_BLOCK])

    def parse_all(self) -> Template:
        body = list()
        start_pos = clone(self.peek_token().span.start_pos)
        while True:
            t0 = self.peek_token()
            if t0.type == END_OF_FILE:
                end_pos = clone(t0.span.end_pos)
                break
            else:
                body.append(self.parse())
        return Template(body, span=TextSpan(self.file, start_pos, end_pos))
