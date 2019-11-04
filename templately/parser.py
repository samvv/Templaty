
from .scanner import *
from .ast import *
from .util import *

PRECEDENCE_TABLE = [
    (2, '<',  1),
    (2, '<=', 1),
    (2, '>',  1), 
    (2, '>=', 1), 
    (2, '!=', 1),
    (2, '==', 1),
    (2, '|',  2),
    (2, '&',  3),
    (2, '<<', 4),
    (2, '>>', 4),
    (2, '+',  5),
    (2, '-',  5),
    (2, '*',  6),
    (2, '/',  6),
    (2, '@',  6),
    (2, '//', 6),
    (2, '%',  6),
    (1, '-',  7),
    (1, '*',  7),
    (1, '~',  7),
    (2, '**', 8)
    ]

def is_right_assoc(name):
    return name == '**'

def get_operator_precedence(name, arity):
    try:
        return next(prec for (arity2, name2, prec) in PRECEDENCE_TABLE if name == name2 and arity == arity2)
    except StopIteration:
        return None

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
        self._statement_stack = []

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
        return VarPattern(t0.value)

    def parse_func_args(self):
        first = True
        while True:
            t0 = self.peek_token()
            if t0.type == END_OF_FILE:
                raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [CLOSE_PAREN], t0)
            elif t0.type == CLOSE_PAREN:
                break
            else:
                if not first:
                    if t0.type != COMMA:
                        raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [COMMA], self._get_text(t0))
                    self.get_token()
                else:
                    first = False
                yield self.parse_expression()

    def parse_func_app(self, e):
        t0 = self.get_token()
        if t0.type != OPEN_PAREN:
            raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [OPEN_PAREN], self._get_text(t0))
        args = list(self.parse_func_args())
        t1 = self.get_token()
        if t1.type != CLOSE_PAREN:
            raise ParseError(self._scanner.get_filename(), t1.start_pos, t1.end_pos, [CLOSE_PAREN], self._get_text(t1))
        return AppExpression(e, args)

    def parse_app_expression(self):
        e = self.parse_prim_expression()
        t1 = self.peek_token()
        if t1.type == OPEN_PAREN:
            return self.parse_func_app(e)
        elif t1.type == OPEN_BRACKET:
            return self.parse_arr_expr(e)
        else:
            return e

    def parse_unary_expression(self):
        heap = []
        while True:
            t0 = self.peek_token()
            if t0.type == OPERATOR:
                t0_prec = get_opeator_info(t0.value, 1)
                heapq.heappush((t0_prec, t0))
            else:
                break
        e = self.parse_app_expression()
        while len(heap) > 0:
            e = AppExpression(VarRefExpression(heappop(heap)[1]), [e])
        return e

    def parse_prim_expression(self):
        t0 = self.get_token()
        if t0.type == OPEN_PAREN:
            e = self.parse_expression()
            t1 = self.get_token()
            if t1.type != CLOSE_PAREN:
                raise ParseError(self._scanner.get_filename(), t1.start_pos, t1.end_pos, [CLOSE_PAREN], self._get_text(t1))
            return e
        elif t0.type == INTEGER:
            return ConstExpression(t0.value)
        elif t0.type == IDENTIFIER:
            return VarRefExpression(self._get_text(t0))
        else:
            raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [IDENTIFIER, INTEGER, OPEN_PAREN], self._get_text(t0))

    def parse_binary_operators(self, lhs, min_prec):
        t0 = self.peek_token()
        while True:
            if t0.type != OPERATOR:
                break
            keep = t0
            keep_prec = get_operator_precedence(keep.value, 2)
            if keep_prec is None:
                break
            self.get_token()
            rhs = self.parse_unary_expression()
            t0 = self.peek_token()
            while True:
                if not t0.type == OPERATOR:
                    break
                t0_prec = get_operator_precedence(t0.value, 2)
                if not (t0_prec is not None and (t0_prec > keep_prec or (is_right_assoc(t0.value) and t0_prec == keep_prec))):
                    break
                rhs = self.parse_binary_operators(rhs, t0_prec)
                t0 = self.peek_token()
            lhs = AppExpression(VarRefExpression(t0), [lhs, rhs])
        return lhs

    def parse_expression(self):
        return self.parse_binary_operators(self.parse_app_expression(), 0)

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
            self._statement_stack.append(FOR_KEYWORD)
            patt = self.parse_pattern()
            t2 = self.get_token()
            if t2.type != IN_KEYWORD:
                raise ParseError(self._scanner.get_filename(), t2.start_pos, t2.end_pos, [IN_KEYWORD], self._get_text(t2))
            e = self.parse_expression()
            t3 = self.get_token()
            if t3.type != CLOSE_STATEMENT_BLOCK:
                raise ParseError(self._scanner.get_filename(), t3.start_pos, t3.end_pos, [CLOSE_STATEMENT_BLOCK], self._get_text(t3))
            body = list(self.parse_body_statements(t0.type))
            t4 = self.get_token()
            if t4.type != t0.type:
                raise ParseError(self._scanner.get_filename(), t4.start_pos, t4.end_pos, [t0.type], self._get_text(t4))
            t5 = self.get_token()
            if t5.type != ENDFOR_KEYWORD:
                raise ParseError(self._scanner.get_filename(), t5.start_pos, t5.end_pos, [ENDFOR_KEYWORD], self._get_text(t5))
            t6 = self.get_token()
            if t6.type != CLOSE_STATEMENT_BLOCK:
                raise ParseError(self._scanner.get_filename(), t6.start_pos, t6.end_pos, [CLOSE_STATEMENT_BLOCK], self._get_text(t5))
            return ForInStatement(patt, e, body)

    def parse_body_statements(self, open_tt):
        while True:
            t0 = self.peek_token()
            if t0.type == open_tt:
                break
            else:
                yield self.parse()

    def parse(self):
        t0 = self.peek_token()
        if t0.type == TEXT:
            self.get_token()
            return TextStatement(self._get_text(t0))
        elif t0.type == OPEN_EXPRESSION_BLOCK:
            return self.parse_expression_block()
        elif t0.type == OPEN_STATEMENT_BLOCK or t0.type == OPEN_STATEMENT_BLOCK_STRIP or t0.type == OPEN_STATEMENT_BLOCK_STRIP_LEFT or t0.type == OPEN_STATEMENT_BLOCK_STRIP_RIGHT:
            return self.parse_statement()
        else:
            raise ParseError(self._scanner.get_filename(), t0.start_pos, t0.end_pos, [TEXT, OPEN_EXPRESSION_BLOCK, OPEN_STATEMENT_BLOCK, OPEN_STATEMENT_BLOCK_STRIP, OPEN_STATEMENT_BLOCK_STRIP_LEFT, OPEN_STATEMENT_BLOCK_STRIP_RIGHT], self._get_text(t0))

    def parse_all(self):
        while True:
            t0 = self.peek_token()
            if t0.type == END_OF_FILE:
                break
            else:
                yield self.parse()

