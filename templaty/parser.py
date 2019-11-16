# Copyright 2019 Sam Vervaeck
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import textwrap
import ast
import heapq

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

def is_right_assoc(name):
    return name == '**'

def is_operator(token_type, arity):
    for (arity_2, token_type_2, prec) in PRECEDENCE_TABLE:
        if token_type_2 == token_type and arity_2 == arity:
            return True
    return False

def get_operator_precedence(token_type, arity):
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

    def __init__(self, filename, start_pos, end_pos, expected, actual):
        super().__init__("{}:{}:{}: Expected {} but got '{}'".format(filename, start_pos.line, start_pos.column, enum_or(token_type_to_string(tt) for tt in expected), actual))
        self._start_pos = start_pos
        self._end_pos = end_pos
        self._expected = expected
        self._actual = actual

    @property
    def start_pos(self):
        return self._start_pos

    @property
    def end_pos(self):
        return self._end_pos

class Parser:

    def __init__(self, scanner):
        self._scanner = scanner
        self._token_stream = scanner.scan()
        self._token_buffer = []
        self._statement_stack = []

    def peek_token(self, count=1):
        while len(self._token_buffer) < count:
            t0 = next(self._token_stream)
            self._token_buffer.append(t0)
        return self._token_buffer[count-1]

    def get_token(self):
        if len(self._token_buffer) > 0:
            return self._token_buffer.pop(0)
        return next(self._token_stream)

    def parse_pattern(self):
        t0 = self.get_token()
        if t0.type != IDENTIFIER:
            self._raise_parse_error(t0, [IDENTIFIER])
        return VarPattern(t0.value)

    def parse_member_expression(self, e):
        self._expect_token(DOT)
        t0 = self.get_token()
        if t0.type != IDENTIFIER:
            self._raise_parse_error(t1, [IDENTIFIER])
        if isinstance(e, MemberExpression):
            e.path.append(t0.value)
        else:
            e = MemberExpression(e, [t0.value])
        return e

    def parse_func_args(self):
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

    def parse_app_expression(self, e):
        self._expect_token(OPEN_PAREN)
        args = list(self.parse_func_args())
        self._expect_token(CLOSE_PAREN)
        return AppExpression(e, args)

    def parse_slice_expression(self, e):
        self._expect_token(OPEN_BRACKET)
        t0 = self.peek_token()
        if t0.type == COLON:
            e1 = None
        else:
            e1 = self.parse_expression()
        t1 = self.get_token()
        if t1.type == CLOSE_BRACKET:
            assert(e1 is not None)
            return IndexExpression(e, e1)
        elif t1.type == COLON:
            t2 = self.peek_token()
            if t2.type == CLOSE_BRACKET:
                e2 = None
            else:
                e2 = self.parse_expression()
            self._expect_token(CLOSE_BRACKET)
            return SliceExpression(e, e1, e2)
        else:
            self._raise_parse_error(t1, [COLON, CLOSE_BRACKET])

    def parse_chained_expression(self):
        e = self.parse_prim_expression()
        while True:
            t1 = self.peek_token()
            if t1.type == DOT:
                e = self.parse_member_expression(e)
            elif t1.type == OPEN_PAREN:
                e = self.parse_app_expression(e)
            elif t1.type == OPEN_BRACKET:
                e = self.parse_slice_expression(e)
            else:
                break
        return e

    def parse_unary_expression(self):
        heap = []
        while True:
            t0 = self.peek_token()
            if is_operator(t0.type, 1):
                print("HERE")
                self.get_token()
                t0_prec = get_operator_precedence(t0.type, 1)
                heapq.heappush(heap, (t0_prec, t0))
            else:
                break
        e = self.parse_chained_expression()
        while len(heap) > 0:
            e = AppExpression(VarRefExpression(heapq.heappop(heap)[1].value), [e])
        return e

    def parse_prim_expression(self):
        t0 = self.get_token()
        if t0.type == OPEN_PAREN:
            e = self.parse_expression()
            self._expect_token(CLOSE_PAREN)
            return e
        elif t0.type == STRING_LITERAL:
            return ConstExpression(t0.value)
        elif t0.type == INTEGER:
            return ConstExpression(t0.value)
        elif t0.type == IDENTIFIER:
            return VarRefExpression(t0.value)
        else:
            self._raise_parse_error(t0, [IDENTIFIER, STRING_LITERAL, INTEGER, OPEN_PAREN])

    def parse_binary_operators(self, lhs, min_prec):
        t0 = self.peek_token()
        while True:
            if not is_operator(t0.type, 2):
                break
            keep = t0
            keep_prec = get_operator_precedence(keep.type, 2)
            if keep_prec is None:
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
            lhs = AppExpression(VarRefExpression(keep.value), [lhs, rhs])
        return lhs

    def parse_expression(self):
        return self.parse_binary_operators(self.parse_unary_expression(), 0)

    def parse_expression_block(self):
        self._expect_token(OPEN_EXPRESSION_BLOCK)
        e = self.parse_expression()
        self._expect_token(CLOSE_EXPRESSION_BLOCK)
        return ExpressionStatement(e)

    def _raise_parse_error(self, token, expected):
        raise ParseError(self._scanner.get_filename(), token.start_pos, token.end_pos, expected, self._get_text(token))

    def _get_text(self, token):
        return token.get_text(self._scanner._data)

    def _expect_token(self, tt):
        t0 = self.get_token()
        if t0.type != tt:
            self._raise_parse_error(t0, [tt])

    def parse_statement(self):
        self._expect_token(OPEN_STATEMENT_BLOCK)
        t1 = self.get_token()
        if t1.type == IF_KEYWORD:
            self._statement_stack.append([ENDIF_KEYWORD, ELIF_KEYWORD, ELSE_KEYWORD])
            cond = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            then = list(self.parse_statement_block())
            cases = [(cond, then)]
            alt = None
            while True:
                self._expect_token(OPEN_STATEMENT_BLOCK)
                t2 = self.get_token()
                if t2.type == ELIF_KEYWORD:
                    cond = self.parse_expression()
                    self._expect_token(CLOSE_STATEMENT_BLOCK)
                    then = list(self.parse_statement_block())
                    cases.append((cond, then))
                elif t2.type == ELSE_KEYWORD:
                    self._expect_token(CLOSE_STATEMENT_BLOCK)
                    self._statement_stack[-1] = [ENDIF_KEYWORD]
                    alt = list(self.parse_statement_block())
                    self._expect_token(OPEN_STATEMENT_BLOCK)
                    self._expect_token(ENDIF_KEYWORD)
                    self._expect_token(CLOSE_STATEMENT_BLOCK)
                    break
                elif t2.type == ENDIF_KEYWORD:
                    self._expect_token(CLOSE_STATEMENT_BLOCK)
                    break
            return IfStatement(cases, alt)
        elif t1.type == FOR_KEYWORD:
            self._statement_stack.append([ENDFOR_KEYWORD])
            patt = self.parse_pattern()
            self._expect_token(IN_KEYWORD)
            e = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = list(self.parse_statement_block())
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDFOR_KEYWORD)
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            return ForInStatement(patt, e, body)
        elif t1.type == JOIN_KEYWORD:
            self._statement_stack.append([ENDJOIN_KEYWORD])
            patt = self.parse_pattern()
            self._expect_token(IN_KEYWORD)
            e = self.parse_expression()
            self._expect_token(WITH_KEYWORD)
            sep = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = list(self.parse_statement_block())
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDJOIN_KEYWORD)
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            return JoinStatement(patt, e, sep, body)
        elif t1.type == SETINDENT_KEYWORD:
            self._statement_stack.append([ENDSETINDENT_KEYWORD])
            e = self.parse_expression()
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = list(self.parse_statement_block())
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDSETINDENT_KEYWORD)
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            return SetIndentStatement(e, body)
        elif t1.type == NOINDENT_KEYWORD:
            self._statement_stack.append([ENDNOINDENT_KEYWORD])
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            body = list(self.parse_statement_block())
            self._expect_token(OPEN_STATEMENT_BLOCK)
            self._expect_token(ENDNOINDENT_KEYWORD)
            self._expect_token(CLOSE_STATEMENT_BLOCK)
            return SetIndentStatement(ConstExpression(0), body)
        else:
            expected = [FOR_KEYWORD, JOIN_KEYWORD, IF_KEYWORD, NOINDENT_KEYWORD, SETINDENT_KEYWORD]
            if len(self._statement_stack) > 0:
                expected.extend(self._statement_stack[-1])
            self._raise_parse_error(t1, expected)

    def parse_statement_block(self):
        close_tts = self._statement_stack[-1]
        while True:
            t0 = self.peek_token(1)
            t1 = self.peek_token(2)
            if t0.type == OPEN_STATEMENT_BLOCK and t1.type in close_tts:
                break
            else:
                yield self.parse()

    def parse_code_block(self):
        stmts = []
        self._expect_token(OPEN_CODE_BLOCK)
        t0 = self.get_token()
        if t0.type != CODE_BLOCK_CONTENT:
            self._raise_parse_error(t0, [CODE_BLOCK_CONTENT])
        module = ast.parse(textwrap.dedent(t0.value))
        self._expect_token(CLOSE_CODE_BLOCK)
        return CodeBlock(module)

    def parse(self):
        t0 = self.peek_token()
        if t0.type == TEXT:
            self.get_token()
            return TextStatement(self._get_text(t0))
        elif t0.type == OPEN_CODE_BLOCK:
            return self.parse_code_block()
        elif t0.type == OPEN_EXPRESSION_BLOCK:
            return self.parse_expression_block()
        elif t0.type == OPEN_STATEMENT_BLOCK:
            return self.parse_statement()
        else:
            self._raise_parse_error(t0, [TEXT, OPEN_EXPRESSION_BLOCK, OPEN_STATEMENT_BLOCK])

    def parse_all(self):
        while True:
            t0 = self.peek_token()
            if t0.type == END_OF_FILE:
                break
            else:
                yield self.parse()

