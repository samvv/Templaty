
import re

def is_space(ch):
    return ch == '\t' or ch == '\n' or ch == '\r' or ch == ' '

def is_id_start(ch):
    return re.match(r'^[a-zA-Z]$', ch) is not None

def is_id_part(ch):
    return re.match(r'^[a-zA-Z0-9]$', ch) is not None

EOF = -1

TEXT                   = 0
IDENTIFIER             = 1
STRING_LITERAL         = 3
BOOLEAN                = 4
IN_KEYWORD             = 5
FOR_KEYWORD            = 6
WHILE_KEYWORD          = 7
ENDFOR_KEYWORD         = 8
ENDWHILE_KEYWORD       = 9
OPEN_EXPRESSION_BLOCK  = 10
CLOSE_EXPRESSION_BLOCK = 11
OPEN_STATEMENT_BLOCK   = 12
CLOSE_STATEMENT_BLOCK  = 13
END_OF_FILE            = 14

KEYWORDS = { 'for': FOR_KEYWORD, 'in': IN_KEYWORD, 'while': WHILE_KEYWORD, 'endfor': ENDFOR_KEYWORD, 'endwhile': ENDWHILE_KEYWORD }

TEXT_MODE = 0
CODE_MODE = 1

def token_type_to_string(tt):
    if tt == IDENTIFIER:
        return 'an identifier'
    elif tt == KEYWORD:
        return 'a keyword'
    elif tt == STRING_LITERAL:
        return 'a string literal'
    elif tt == BOOLEAN:
        return "'True' or 'False'"

class Position:

    def __init__(self, offset=0, line=1, column=1):
        self.offset = offset
        self.line = line
        self.column = column

    def clone(self):
        return Position(self.offset, self.line, self.column)

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
    def start_pos(self):
        return self._start_pos

    @property
    def end_pos(self):
        return self._end_pos

class ScanError(RuntimeError):

    def __init__(self, filename, start_pos, c0):
        super().__init__("{}:{}:{}: Got an unexpected character '{}'".format(filename, start_pos.line, start_pos.column, c0))
        self._start_pos = start_pos

    @property
    def start_pos(self):
        return self._start_pos

class Scanner:

    def __init__(self, filename, data):
        self._ch = None
        self._data = data
        self._offset = 0
        self._filename = filename
        self._curr_pos = Position()
        self._mode = TEXT_MODE

    def get_filename(self):
        return self._filename

    def read_char(self):
        if self._offset == len(self._data):
            return EOF
        ch = self._data[self._offset]
        self._offset += 1
        return ch

    def peek_char(self):
        if self._ch is None:
            ch = self.read_char()
            self._ch = ch
            return ch
        else:
            return self._ch

    def get_char(self):
        if self._ch is None:
            ch = self.read_char()
        else:
            ch = self._ch
            self._ch = None
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
        return None # TODO

    def scan(self):
        if self._mode == TEXT_MODE:
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
                        self._mode = CODE_MODE
                        self.get_char()
                        return Token(OPEN_EXPRESSION_BLOCK, start_pos, self._curr_pos.clone())
                    elif ch1 == '%':
                        self._mode = CODE_MODE
                        self.get_char()
                        return Token(OPEN_STATEMENT_BLOCK, start_pos, self._curr_pos.clone())
                    else:
                        text += ch0
                else:
                    self.get_char()
                    text += ch0
        elif self._mode == CODE_MODE:
            self.skip_ws()
            start_pos = self._curr_pos.clone()
            c0 = self.peek_char()
            if c0 == '%':
                self.get_char()
                c1 = self.peek_char()
                if c1 == '}':
                    self.get_char()
                    self._mode = TEXT_MODE
                    return Token(CLOSE_STATEMENT_BLOCK, start_pos, self._curr_pos.clone())
                else:
                    return Token(OPERATOR, start_pos, self._curr_pos.clone(), '%')
            elif c0 == '}':
                self.get_char()
                c1 = self.peek_char()
                if c1 == '}':
                    self.get_char()
                    self._mode = TEXT_MODE
                    return Token(CLOSE_EXPRESSION_BLOCK, start_pos, self._curr_pos.clone())
                else:
                    raise ScanError(self._filename, self._curr_pos.clone(), c0)
            elif c0 == '\'':
                return self.scan_string_lit()
            elif is_id_start(c0):
                name = self.scan_raw_identifier()
                if name in KEYWORDS:
                    return Token(KEYWORDS[name], start_pos, self._curr_pos.clone(), name)
                else:
                    return Token(IDENTIFIER, start_pos, self._curr_pos.clone(), name)
            else:
                raise ScanError(self._filename, self._curr_pos.clone(), c0)

    def scan_all(self): 
        while True:
            t1 = self.scan()
            if t1.type == END_OF_FILE:
                break
            else:
                yield t1

