
from .scanner import *
from .ast import *
from .util import *

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
        self._token_buffer = []

    def peek_token(self):
        if len(self._token_buffer) > 0:
            return self._token_buffer[0]
        t0 = self._scanner.scan()
        self._token_buffer.append(t0)
        return t0

    def get_token(self):
        if len(self._token_buffer) > 0:
            return self._token_buffer.pop(0)
        return self._scanner.scan()

    def parse_pattern(self):
        t0 = self.get_token()
        if t0.type != IDENTIFIER:
            raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [IDENTIFIER], self._get_text(t0))
        return VarPattern(t0)

    def parse_expression(self):
        t0 = self.get_token()
        if t0.type == IDENTIFIER:
            return VarRefExpression(t0)
        raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [IDENTIFIER], self._get_text(t0))

    def parse_expression_block(self):
        t0 = self.get_token()
        if t0.type != OPEN_EXPRESSION_BLOCK:
            raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [OPEN_EXPRESSION_BLOCK], self._get_text(t0))
        e = self.parse_expression()
        t1 = self.get_token()
        if t1.type != CLOSE_EXPRESSION_BLOCK:
            raise ParseError(self._scanner.get_filename(), t1.start_pos, t1.end_pos, [CLOSE_EXPRESSION_BLOCK], self._get_text(t1))
        return e

    def _get_text(self, token):
        return token.get_text(self._scanner._data)

    def parse_statement(self):
        t0 = self.get_token()
        if t0.type != OPEN_STATEMENT_BLOCK:
            raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [OPEN_STATEMENT_BLOCK], self._get_text(t0))
        t1 = self.get_token()
        if t1.type == FOR_KEYWORD:
            patt = self.parse_pattern()
            t2 = self.get_token()
            if t2.type != IN_KEYWORD:
                raise ParseError(self._scanner.get_filename(), t2.start_pos, t2.end_pos, [IN_KEYWORD], self._get_text(t2))
            e = self.parse_expression()
            t3 = self.get_token()
            if t3.type != CLOSE_STATEMENT_BLOCK:
                raise ParseError(self._scanner.get_filename(), t3.start_pos, t3.end_pos, [CLOSE_STATEMENT_BLOCK], self._get_text(t3))
            body = list(self.parse_body_statements())
            t4 = self.get_token()
            if t4.type != OPEN_STATEMENT_BLOCK:
                raise ParseError(self._scanner.get_filename(), t4.start_pos, t4.end_pos, [OPEN_STATEMENT_BLOCK], self._get_text(t4))
            t5 = self.get_token()
            if t5.type != ENDFOR_KEYWORD:
                raise ParseError(self._scanner.get_filename(), t5.start_pos, t5.end_pos, [ENDFOR_KEYWORD], self._get_text(t5))
            t6 = self.get_token()
            if t6.type != CLOSE_STATEMENT_BLOCK:
                raise ParseError(self._scanner.get_filename(), t6.start_pos, t6.end_pos, [CLOSE_STATEMENT_BLOCK], self._get_text(t5))
            return ForInStatement(patt, e, body)

    def parse_body_statements(self):
        while True:
            t0 = self.peek_token()
            if t0.type == OPEN_STATEMENT_BLOCK:
                break
            else:
                yield self.parse()

    def parse(self):
        t0 = self.peek_token()
        if t0.type == END_OF_FILE:
            return None
        elif t0.type == TEXT:
            self.get_token()
            return t0
        elif t0.type == OPEN_EXPRESSION_BLOCK:
            return self.parse_expression_block()
        elif t0.type == OPEN_STATEMENT_BLOCK:
            return self.parse_statement()
        else:
            raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [TEXT, OPEN_EXPRESSION_BLOCK, OPEN_STATEMENT_BLOCK], self._get_text(t0))

    def parse_all(self):
        while True:
            s1 = self.parse()
            if s1 is None:
                break
            else:
                yield s1

