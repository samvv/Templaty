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

import re
from typing import Any, Generator, Optional
from sweetener import NewType, Record, TextFile, clone

from .ast import TextPos, TextSpan
from .util import escape

def is_space(ch: str) -> bool:
    return ch == '\t' or ch == '\n' or ch == '\r' or ch == ' '

def is_id_start(ch: str) -> bool:
    return ch != EOF and re.match(r'^[a-zA-Z_]$', ch) is not None

def is_id_part(ch: str) -> bool:
    return ch != EOF and re.match(r'^[a-zA-Z0-9_]$', ch) is not None

def is_digit(ch: str) -> bool:
    return ch != EOF and re.match(r'^[0-9]$', ch) is not None

def pretty_char(ch: str) -> str:
    if ch == EOF:
        return 'end-of-file'
    else:
        return f'{escape(ch)}'

EOF = '\uFFFF'

TokenType = NewType('TokenType', int)

TEXT                              = TokenType(0)
IDENTIFIER                        = TokenType(1)
STRING_LITERAL                    = TokenType(3)
BOOLEAN                           = TokenType(4)
IN_KEYWORD                        = TokenType(5)
FOR_KEYWORD                       = TokenType(6)
WHILE_KEYWORD                     = TokenType(7)
ENDFOR_KEYWORD                    = TokenType(8)
ENDWHILE_KEYWORD                  = TokenType(9)
OPEN_EXPRESSION_BLOCK             = TokenType(10)
CLOSE_EXPRESSION_BLOCK            = TokenType(11)
OPEN_STATEMENT_BLOCK              = TokenType(12)
CLOSE_STATEMENT_BLOCK             = TokenType(13)
END_OF_FILE                       = TokenType(14)
OPEN_PAREN                        = TokenType(15)
CLOSE_PAREN                       = TokenType(16)
OPEN_BRACKET                      = TokenType(18)
CLOSE_BRACKET                     = TokenType(19)
INTEGER                           = TokenType(20)
COMMA                             = TokenType(21)
JOIN_KEYWORD                      = TokenType(22)
ENDJOIN_KEYWORD                   = TokenType(23)
WITH_KEYWORD                      = TokenType(24)
IF_KEYWORD                        = TokenType(25)
ELSE_KEYWORD                      = TokenType(26)
ENDIF_KEYWORD                     = TokenType(27)
ELIF_KEYWORD                      = TokenType(28)
OPEN_CODE_BLOCK                   = TokenType(29)
CLOSE_CODE_BLOCK                  = TokenType(30)
DOT                               = TokenType(31)
NOINDENT_KEYWORD                  = TokenType(32)
SETINDENT_KEYWORD                 = TokenType(33)
DEDENT_KEYWORD                    = TokenType(34)
ENDNOINDENT_KEYWORD               = TokenType(35)
ENDSETINDENT_KEYWORD              = TokenType(36)
ENDDEDENT_KEYWORD                 = TokenType(37)
CODE_BLOCK_CONTENT                = TokenType(38)
COLON                             = TokenType(39)
ADD_OPERATOR                      = TokenType(40)
SUB_OPERATOR                      = TokenType(41)
MUL_OPERATOR                      = TokenType(42)
DIV_OPERATOR                      = TokenType(43)
EXP_OPERATOR                      = TokenType(44)
REM_OPERATOR                      = TokenType(45)
MOD_OPERATOR                      = TokenType(46)
LSHIFT_OPERATOR                   = TokenType(47)
RSHIFT_OPERATOR                   = TokenType(48)
BAND_OPERATOR                     = TokenType(49)
BOR_OPERATOR                      = TokenType(50)
BXOR_OPERATOR                     = TokenType(51)
BNOT_OPERATOR                     = TokenType(52)
LT_OPERATOR                       = TokenType(53)
GT_OPERATOR                       = TokenType(54)
LTE_OPERATOR                      = TokenType(55)
GTE_OPERATOR                      = TokenType(56)
EQ_OPERATOR                       = TokenType(57)
NEQ_OPERATOR                      = TokenType(58)
PIPE_OPERATOR                     = TokenType(59)
AND_OPERATOR                      = TokenType(60)
OR_OPERATOR                       = TokenType(61)
NOT_OPERATOR                      = TokenType(62)
AT                                = TokenType(63)
COMMENT                           = TokenType(64)

OPERATORS = {
    '+': ADD_OPERATOR,
    '-': SUB_OPERATOR,
    '*': MUL_OPERATOR,
    '/': DIV_OPERATOR,
    '**': EXP_OPERATOR,
    '//': REM_OPERATOR,
    '%': MOD_OPERATOR,
    '<<': LSHIFT_OPERATOR,
    '>>': RSHIFT_OPERATOR,
    '&': BAND_OPERATOR,
    '|': BOR_OPERATOR,
    '^': BXOR_OPERATOR,
    '~': BNOT_OPERATOR,
    '<': LT_OPERATOR,
    '>': GT_OPERATOR,
    '<=': LTE_OPERATOR,
    '>=': GTE_OPERATOR,
    '|>': PIPE_OPERATOR,
    '==': EQ_OPERATOR,
    '!=': NEQ_OPERATOR
    }

def is_operator_start(ch):
    matcher = re.compile(r"^[+\-*/%<>&|^~=]$")
    return matcher.match(ch)

def is_operator_part(ch):
    matcher = re.compile(r"^[*/=>]$")
    return matcher.match(ch)

KEYWORDS = { 
    'for': FOR_KEYWORD, 
    'in': IN_KEYWORD, 
    'while': WHILE_KEYWORD, 
    'endfor': ENDFOR_KEYWORD, 
    'endwhile': ENDWHILE_KEYWORD, 
    'join': JOIN_KEYWORD, 
    'endjoin': ENDJOIN_KEYWORD,
    'with': WITH_KEYWORD,
    'if': IF_KEYWORD,
    'else': ELSE_KEYWORD,
    'endif': ENDIF_KEYWORD,
    'elif': ELIF_KEYWORD,
    'noindent': NOINDENT_KEYWORD,
    'endnoindent': ENDNOINDENT_KEYWORD,
    'setindent': SETINDENT_KEYWORD,
    'endsetindent': ENDSETINDENT_KEYWORD,
    'dedent': DEDENT_KEYWORD,
    'enddedent': ENDDEDENT_KEYWORD
    }

NAMED_OPERATORS = {
    'not': NOT_OPERATOR,
    'and': AND_OPERATOR,
    'or': OR_OPERATOR
    }

TEXT_MODE = 0
STATEMENT_MODE = 1
CODE_BLOCK_MODE = 2

def token_type_to_string(tt):
    if tt == IDENTIFIER:
        return 'an identifier'
    elif tt == FOR_KEYWORD:
        return "'for'"
    elif tt == IN_KEYWORD:
        return "'in'"
    elif tt == ENDFOR_KEYWORD:
        return "'endfor'"
    elif tt == WHILE_KEYWORD:
        return "'while'"
    elif tt == ENDWHILE_KEYWORD:
        return "'while'"
    elif tt == STRING_LITERAL:
        return 'a string literal'
    elif tt == BOOLEAN:
        return "'True' or 'False'"
    elif tt == OPEN_EXPRESSION_BLOCK:
        return "'{{'"
    elif tt == CLOSE_EXPRESSION_BLOCK:
        return "'}}'"
    elif tt == OPEN_STATEMENT_BLOCK:
        return "'{%'"
    elif tt == CLOSE_STATEMENT_BLOCK:
        return "'%}'"
    elif tt == TEXT:
        return "some text"
    elif tt == OPEN_PAREN:
        return "'('"
    elif tt == CLOSE_PAREN:
        return "')'"
    elif tt == OPEN_BRACKET:
        return "'['"
    elif tt == CLOSE_BRACKET:
        return "']'"
    elif tt == INTEGER:
        return 'an integer'
    elif tt == JOIN_KEYWORD:
        return "'join'"
    elif tt == ENDJOIN_KEYWORD:
        return "'endjoin'"
    elif tt == WITH_KEYWORD:
        return "'with'"
    elif tt == IF_KEYWORD:
        return "'if'"
    elif tt == ELSE_KEYWORD:
        return "'else'"
    elif tt == ENDIF_KEYWORD:
        return "'endif'"
    elif tt == NOINDENT_KEYWORD:
        return "'noindent'"
    elif tt == SETINDENT_KEYWORD:
        return "'setindent'"
    elif tt == ENDNOINDENT_KEYWORD:
        return "'endnoindent'"
    elif tt == ENDSETINDENT_KEYWORD:
        return "'endsetindent'"
    elif tt == ADD_OPERATOR:
        return "'+'"
    elif tt == SUB_OPERATOR:
        return "'-'"
    elif tt == MUL_OPERATOR:
        return "'*'"
    elif tt == DIV_OPERATOR:
        return "'/'"
    elif tt == EXP_OPERATOR:
        return "'**'"
    elif tt == REM_OPERATOR:
        return "'//'"
    elif tt == MOD_OPERATOR:
        return "'%'"
    elif tt == LSHIFT_OPERATOR:
        return "'<<'"
    elif tt == RSHIFT_OPERATOR:
        return "'>>'"
    elif tt == BAND_OPERATOR:
        return "'&'"
    elif tt == BOR_OPERATOR:
        return "'|'"
    elif tt == BXOR_OPERATOR:
        return "'^'"
    elif tt == BNOT_OPERATOR:
        return "'~'"
    elif tt == LT_OPERATOR:
        return "'<'"
    elif tt == GT_OPERATOR:
        return "'>'"
    elif tt == LTE_OPERATOR:
        return "'<='"
    elif tt == GTE_OPERATOR:
        return "'>='"
    elif tt == EQ_OPERATOR:
        return "'=='"
    elif tt == NEQ_OPERATOR:
        return "'!='"
    elif tt == PIPE_OPERATOR:
        return "'|>'"
    elif tt == AND_OPERATOR:
        return "'and'"
    elif tt == OR_OPERATOR:
        return "'or'"
    elif tt == NOT_OPERATOR:
        return "'not'"
    elif tt == AT:
        return "'@'"

class Token(Record):

    type: TokenType
    span: TextSpan
    value: Optional[Any] = None

    @property
    def text(self):
        return self.span.file.text[self.span.start_pos.offset:self.span.end_pos.offset]

class ScanError(RuntimeError):

    def __init__(self, filename, start_pos, c0):
        super().__init__("{}:{}:{}: Got an unexpected {}".format(filename, start_pos.line, start_pos.column, pretty_char(c0)))
        self.start_pos = start_pos

class Scanner:

    def __init__(self, filename: str, data: str, is_code=False):
        self._buffer = []
        self._data = data
        self.file = TextFile(data, name=filename)
        self._offset = 0
        self._filename = filename
        self._curr_pos = TextPos()
        self._mode = STATEMENT_MODE if is_code else TEXT_MODE 

    def get_filename(self) -> str:
        return self._filename

    def read_char(self) -> str:
        if self._offset == len(self._data):
            return EOF
        ch = self._data[self._offset]
        self._offset += 1
        return ch

    def peek_char(self, offset=1) -> str:
        while len(self._buffer) < offset:
            c0 = self.read_char()
            if c0 == EOF:
                return EOF
            self._buffer.append(c0)
        return self._buffer[offset-1]

    def get_char(self) -> str:
        if len(self._buffer) == 0:
            ch = self.read_char()
        else:
            ch = self._buffer.pop(0)
        if ch == '\n':
            self._curr_pos.line += 1
            self._curr_pos.column = 1
        else:
            self._curr_pos.column += 1
        self._curr_pos.offset += 1
        return ch

    def scan_raw_identifier(self) -> str:
        c0 = self.get_char()
        if not is_id_start(c0):
            raise ScanError(self._filename, clone(self._curr_pos), c0)
        name = c0
        while True:
            ch1 = self.peek_char()
            if is_id_part(ch1):
                self.get_char()
                name += ch1
            else:
                break
        return name

    def skip_ws(self) -> None:
        while is_space(self.peek_char()):
            self.get_char()

    def scan_string_lit(self) -> Token:
        value = ''
        start_pos = clone(self._curr_pos)
        escaping = False
        c0 = self.get_char()
        if c0 != '\'':
            raise ScanError(self._filename, clone(self._curr_pos), c0)
        while True:
            ch = self.get_char()
            if ch == '\'':
                break
            elif ch == '\\':
                escaping = True
                continue
            if escaping:
                value += unescape(ch)
            else:
                value += ch
        return Token(STRING_LITERAL, TextSpan(self.file, start_pos, clone(self._curr_pos)), value)

    def scan(self) -> Generator[Token, None, None]:

        while True:

            if self._mode == TEXT_MODE:

                text = ''
                start_pos = clone(self._curr_pos)
                while True:
                    ch0 = self.peek_char(1)
                    if ch0 == EOF:
                        if len(text) > 0:
                            yield Token(TEXT, TextSpan(self.file, start_pos, clone(self._curr_pos)), text)
                            text = ''
                        yield Token(END_OF_FILE, TextSpan(self.file, clone(self._curr_pos), clone(self._curr_pos)))
                        break
                    if ch0 == '{':
                        if len(text) > 0:
                            yield Token(TEXT, TextSpan(self.file, start_pos, clone(self._curr_pos)), text)
                            text = ''
                        ch1 = self.peek_char(2)
                        if ch1 == '{':
                            self._mode = STATEMENT_MODE
                            start_pos = clone(self._curr_pos)
                            self.get_char()
                            self.get_char()
                            yield Token(OPEN_EXPRESSION_BLOCK, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                            break
                        elif ch1 == '%':
                            self._mode = STATEMENT_MODE
                            start_pos = clone(self._curr_pos)
                            self.get_char()
                            self.get_char()
                            yield Token(OPEN_STATEMENT_BLOCK, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                            break
                        elif ch1 == '!':
                            self._mode = CODE_BLOCK_MODE
                            start_pos = clone(self._curr_pos)
                            self.get_char()
                            self.get_char()
                            yield Token(OPEN_CODE_BLOCK, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                            break
                        elif ch1 == '#':
                            start_pos = clone(self._curr_pos)
                            self.get_char()
                            self.get_char()
                            comment_text = ''
                            level = 1
                            while True:
                                ch2 = self.peek_char(1)
                                ch3 = self.peek_char(2)
                                if ch2 == EOF:
                                    end_pos = clone(self._curr_pos)
                                    yield Token(COMMENT, TextSpan(self.file, start_pos, end_pos), comment_text)
                                    break
                                if ch2 == '{' and ch3 == '#':
                                    level += 1
                                elif ch2 == '#' and ch3 == '}':
                                    level -= 1
                                    if level == 0:
                                        self.get_char()
                                        self.get_char()
                                        end_pos = clone(self._curr_pos)
                                        yield Token(COMMENT, TextSpan(self.file, start_pos, end_pos), comment_text)
                                        break
                                comment_text += self.get_char()
                    text += self.get_char()

            elif self._mode == CODE_BLOCK_MODE:

                # TODO accept code block string literals that contain '!}'
                in_string_literal = False
                start_pos = clone(self._curr_pos)
                text = ''
                while True:
                    c0 = self.peek_char(1)
                    c1 = self.peek_char(2)
                    if c0 == '!' and c1 == '}':
                        break
                    if c0 == EOF:
                        raise ScanError(self._filename, start_pos, c0)
                    text += self.get_char()
                self._mode = TEXT_MODE
                end_pos = clone(self._curr_pos)
                yield Token(CODE_BLOCK_CONTENT, TextSpan(self.file, start_pos, end_pos), text)
                start_pos = clone(self._curr_pos)
                self.get_char()
                self.get_char()
                end_pos = clone(self._curr_pos)
                yield Token(CLOSE_CODE_BLOCK, TextSpan(self.file, start_pos, end_pos))

            elif self._mode == STATEMENT_MODE:

                self.skip_ws()
                start_pos = clone(self._curr_pos)
                c0 = self.peek_char()
                if c0 == EOF:
                    yield Token(END_OF_FILE, TextSpan(self.file, clone(self._curr_pos), clone(self._curr_pos)))
                elif c0 == ':':
                    self.get_char()
                    yield Token(COLON, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                elif c0 == '.':
                    self.get_char()
                    yield Token(DOT, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                elif c0 == '!':
                    self.get_char()
                    c1 = self.get_char()
                    if c1 == '=':
                        yield Token(NEQ_OPERATOR, TextSpan(self.file, start_pos, clone(self._curr_pos)), '!=')
                    elif c1 == '}':
                        yield Token(CLOSE_CODE_BLOCK, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                    else:
                        raise ScanError(self._filename, clone(self._curr_pos), c0)
                elif c0 == '%':
                    self.get_char()
                    c1 = self.get_char()
                    if c1 == '}':
                        self._mode = TEXT_MODE
                        yield Token(CLOSE_STATEMENT_BLOCK, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                    else:
                        yield Token(MOD_OPERATOR, TextSpan(self.file, start_pos, clone(self._curr_pos)), '%')
                elif c0 == '}':
                    self.get_char()
                    c1 = self.get_char()
                    if c1 == '}':
                        self._mode = TEXT_MODE
                        yield Token(CLOSE_EXPRESSION_BLOCK, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                    else:
                        raise ScanError(self._filename, clone(self._curr_pos), c0)
                elif c0 == ',':
                    self.get_char()
                    yield Token(COMMA, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                elif c0 == '(':
                    self.get_char()
                    yield Token(OPEN_PAREN, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                elif c0 == ')':
                    self.get_char()
                    yield Token(CLOSE_PAREN, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                elif c0 == '[':
                    self.get_char()
                    yield Token(OPEN_BRACKET, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                elif c0 == ']':
                    self.get_char()
                    yield Token(CLOSE_BRACKET, TextSpan(self.file, start_pos, clone(self._curr_pos)))
                elif c0 == '\'':
                    yield self.scan_string_lit()
                elif is_digit(c0):
                    self.get_char()
                    digits = c0
                    while is_digit(self.peek_char()):
                        digits += self.get_char()
                    yield Token(INTEGER, TextSpan(self.file, start_pos, clone(self._curr_pos)), int(digits))
                elif is_operator_start(c0):
                    op = c0
                    self.get_char()
                    while is_operator_part(self.peek_char()): 
                        op += self.get_char()
                    if not op in OPERATORS:
                        raise ScanError(self._filename, start_pos, op)
                    yield Token(OPERATORS[op], TextSpan(self.file, start_pos, clone(self._curr_pos)), op)
                elif is_id_start(c0):
                    name = self.scan_raw_identifier()
                    if name in NAMED_OPERATORS:
                        yield Token(NAMED_OPERATORS[name], TextSpan(self.file, start_pos, clone(self._curr_pos)), name)
                    elif name in KEYWORDS:
                        yield Token(KEYWORDS[name], TextSpan(self.file, start_pos, clone(self._curr_pos)), name)
                    else:
                        yield Token(IDENTIFIER, TextSpan(self.file, start_pos, clone(self._curr_pos)), name)
                else:
                    raise ScanError(self._filename, clone(self._curr_pos), c0)

