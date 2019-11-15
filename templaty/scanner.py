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

from .util import escape

def is_space(ch):
    return ch == '\t' or ch == '\n' or ch == '\r' or ch == ' '

def is_id_start(ch):
    return ch != EOF and re.match(r'^[a-zA-Z_]$', ch) is not None

def is_id_part(ch):
    return ch != EOF and re.match(r'^[a-zA-Z0-9_]$', ch) is not None

def is_digit(ch):
    return ch != EOF and re.match(r'^[0-9]$', ch) is not None

def pretty_char(ch):
    if ch == EOF:
        return 'end-of-file'
    else:
        return f'{escape(ch)}'

EOF = -1

TEXT                              = 0
IDENTIFIER                        = 1
STRING_LITERAL                    = 3
BOOLEAN                           = 4
IN_KEYWORD                        = 5
FOR_KEYWORD                       = 6
WHILE_KEYWORD                     = 7
ENDFOR_KEYWORD                    = 8
ENDWHILE_KEYWORD                  = 9
OPEN_EXPRESSION_BLOCK             = 10
CLOSE_EXPRESSION_BLOCK            = 11
OPEN_STATEMENT_BLOCK              = 12
CLOSE_STATEMENT_BLOCK             = 13
END_OF_FILE                       = 14
OPEN_PAREN                        = 15
CLOSE_PAREN                       = 16
OPERATOR                          = 17
OPEN_BRACKET                      = 18
CLOSE_BRACKET                     = 19
INTEGER                           = 20
COMMA                             = 21
JOIN_KEYWORD                      = 22
ENDJOIN_KEYWORD                   = 23
WITH_KEYWORD                      = 24
IF_KEYWORD                        = 25
ELSE_KEYWORD                      = 26
ENDIF_KEYWORD                     = 27
ELIF_KEYWORD                      = 28
OPEN_CODE_BLOCK                   = 29
CLOSE_CODE_BLOCK                  = 30
DOT                               = 31
NOINDENT_KEYWORD                  = 32
SETINDENT_KEYWORD                 = 33
DEDENT_KEYWORD                    = 34
ENDNOINDENT_KEYWORD               = 35
ENDSETINDENT_KEYWORD              = 36
ENDDEDENT_KEYWORD                 = 37
CODE_BLOCK_CONTENT                = 38
COLON                             = 39

OPERATORS = ['+', '-', '*', '**', '/', '//', '%', '@', '<<', '>>', '&', '|', '^', '~', ':=', '<', '>', '<=', '>=', '==', '!=', '|>']

def is_operator_start(ch):
    for op in OPERATORS:
        if op[0] == ch:
            return True
    return False

def is_operator_part(ch):
    for op in OPERATORS:
        if ch in op[1:]:
            return True
    return False

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
    'enddedent': ENDDEDENT_KEYWORD,
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

class Position:

    def __init__(self, offset=0, line=1, column=1):
        self.offset = offset
        self.line = line
        self.column = column

    def clone(self):
        return Position(self.offset, self.line, self.column)

    def advance(self, text):
        for ch in text:
            if ch == '\n':
                self.line += 1
                self.column = 0
            else:
                self.column += 1
            self.offset += 1

class Token:

    def __init__(self, type, start_pos, end_pos, value=None):
        self._type = type
        self._start_pos = start_pos
        self._end_pos = end_pos
        self._value = value

    def get_text(self, data):
        return data[self._start_pos.offset:self._end_pos.offset]

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        return self._value

    @property
    def start_pos(self):
        return self._start_pos

    @property
    def end_pos(self):
        return self._end_pos

class ScanError(RuntimeError):

    def __init__(self, filename, start_pos, c0):
        super().__init__("{}:{}:{}: Got an unexpected {}".format(filename, start_pos.line, start_pos.column, pretty_char(c0)))
        self._start_pos = start_pos

    @property
    def start_pos(self):
        return self._start_pos

class Scanner:

    def __init__(self, filename, data, is_code=False):
        self._buffer = []
        self._data = data
        self._offset = 0
        self._filename = filename
        self._curr_pos = Position()
        self._mode = STATEMENT_MODE if is_code else TEXT_MODE 

    def get_filename(self):
        return self._filename

    def read_char(self):
        if self._offset == len(self._data):
            return EOF
        ch = self._data[self._offset]
        self._offset += 1
        return ch

    def peek_char(self, offset=1):
        while len(self._buffer) < offset:
            c0 = self.read_char()
            if c0 == EOF:
                return EOF
            self._buffer.append(c0)
        return self._buffer[offset-1]

    def get_char(self):
        if len(self._buffer) == 0:
            ch = self.read_char()
        else:
            ch = self._buffer.pop(0)
        if ch == '\n':
            self._curr_pos.line += 1
            self._curr_pos.column = 0
        else:
            self._curr_pos.column += 1
        self._curr_pos.offset += 1
        return ch

    def scan_raw_identifier(self):
        c0 = self.get_char()
        if not is_id_start(c0):
            raise ScanError(self._filename, self._curr_pos.clone(), c0)
        name = c0
        while True:
            ch1 = self.peek_char()
            if is_id_part(ch1):
                self.get_char()
                name += ch1
            else:
                break
        return name

    def skip_ws(self):
        while is_space(self.peek_char()):
            self.get_char()

    def scan_string_lit(self):
        value = ''
        start_pos = self._curr_pos.clone()
        escaping = False
        c0 = self.get_char()
        if c0 != '\'':
            raise ScanError(self._filename, self._curr_pos.clone(), c0)
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
        return Token(STRING_LITERAL, start_pos, self._curr_pos.clone(), value)

    def scan_raw_text(self):
        text = ''
        start_pos = self._curr_pos.clone()
        while True:
            ch0 = self.peek_char()
            if ch0 == EOF:
                if len(text) > 0:
                    return Token(TEXT, start_pos, self._curr_pos.clone(), text) 
                return Token(END_OF_FILE, self._curr_pos.clone(), self._curr_pos.clone())
            elif ch0 == '{':
                if len(text) > 0:
                    return Token(TEXT, start_pos, self._curr_pos.clone(), text)
                self.get_char()
                ch1 = self.peek_char()
                if ch1 == '{':
                    self._mode = STATEMENT_MODE
                    self.get_char()
                    return Token(OPEN_EXPRESSION_BLOCK, start_pos, self._curr_pos.clone())
                elif ch1 == '%':
                    self._mode = STATEMENT_MODE
                    self.get_char()
                    return Token(OPEN_STATEMENT_BLOCK, start_pos, self._curr_pos.clone())
                elif ch1 == '!':
                    self._mode = CODE_BLOCK_MODE
                    self.get_char()
                    return Token(OPEN_CODE_BLOCK, start_pos, self._curr_pos.clone())
                elif ch1 == '#':
                    self.get_char()
                    while True:
                        ch2 = self.get_char()
                        if ch2 == '#':
                            ch3 = self.get_char()
                            if ch3 == '}':
                                ch4 = self.peek_char()
                                if ch4 == '\n':
                                    self.get_char()
                                start_pos = self._curr_pos.clone()
                                break
                else:
                    text += ch0
            else:
                self.get_char()
                text += ch0

    def scan(self):
        while True:
            if self._mode == TEXT_MODE:
                yield self.scan_raw_text()
            elif self._mode == CODE_BLOCK_MODE:
                in_string_literal = False
                start_pos = self._curr_pos.clone()
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
                end_pos = self._curr_pos.clone()
                yield Token(CODE_BLOCK_CONTENT, start_pos, end_pos, text)
                start_pos = self._curr_pos.clone()
                self.get_char()
                self.get_char()
                end_pos = self._curr_pos.clone()
                yield Token(CLOSE_CODE_BLOCK, start_pos, end_pos)
            elif self._mode == STATEMENT_MODE:
                self.skip_ws()
                start_pos = self._curr_pos.clone()
                c0 = self.peek_char()
                if c0 == EOF:
                    yield Token(END_OF_FILE, self._curr_pos.clone(), self._curr_pos.clone())
                elif c0 == ':':
                    self.get_char()
                    yield Token(COLON, start_pos, self._curr_pos.clone())
                elif c0 == '.':
                    self.get_char()
                    yield Token(DOT, start_pos, self._curr_pos.clone())
                elif c0 == '!':
                    self.get_char()
                    c1 = self.get_char()
                    if c1 == '=':
                        yield Token(OPERATOR, start_pos, self._curr_pos.clone())
                    elif c1 == '}':
                        yield Token(CLOSE_CODE_BLOCK, start_pos, self._curr_pos.clone())
                    else:
                        raise ScanError(self._filename, self._curr_pos.clone(), c0)
                elif c0 == '%':
                    self.get_char()
                    c1 = self.get_char()
                    if c1 == '}':
                        self._mode = TEXT_MODE
                        yield Token(CLOSE_STATEMENT_BLOCK, start_pos, self._curr_pos.clone())
                    else:
                        yield Token(OPERATOR, start_pos, self._curr_pos.clone(), '%')
                elif c0 == '}':
                    self.get_char()
                    c1 = self.get_char()
                    if c1 == '}':
                        self._mode = TEXT_MODE
                        yield Token(CLOSE_EXPRESSION_BLOCK, start_pos, self._curr_pos.clone())
                    else:
                        raise ScanError(self._filename, self._curr_pos.clone(), c0)
                elif c0 == ',':
                    self.get_char()
                    yield Token(COMMA, start_pos, self._curr_pos.clone())
                elif c0 == '(':
                    self.get_char()
                    yield Token(OPEN_PAREN, start_pos, self._curr_pos.clone())
                elif c0 == ')':
                    self.get_char()
                    yield Token(CLOSE_PAREN, start_pos, self._curr_pos.clone())
                elif c0 == '[':
                    self.get_char()
                    yield Token(OPEN_BRACKET, start_pos, self._curr_pos.clone())
                elif c0 == ']':
                    self.get_char()
                    yield Token(CLOSE_BRACKET, start_pos, self._curr_pos.clone())
                elif c0 == '\'':
                    yield self.scan_string_lit()
                elif is_digit(c0):
                    self.get_char()
                    digits = c0
                    while is_digit(self.peek_char()):
                        digits += self.get_char()
                    yield Token(INTEGER, start_pos, self._curr_pos.clone(), int(digits))
                elif is_operator_start(c0):
                    op = c0
                    self.get_char()
                    while is_operator_part(self.peek_char()): 
                        op += self.get_char()
                    if not op in OPERATORS:
                        raise ScanError(self._filename, start_pos, op)
                    yield Token(OPERATOR, start_pos, self._curr_pos.clone(), op)
                elif is_id_start(c0):
                    name = self.scan_raw_identifier()
                    if name in KEYWORDS:
                        yield Token(KEYWORDS[name], start_pos, self._curr_pos.clone(), name)
                    else:
                        yield Token(IDENTIFIER, start_pos, self._curr_pos.clone(), name)
                else:
                    raise ScanError(self._filename, self._curr_pos.clone(), c0)

