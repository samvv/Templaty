
class Text:

    def __init__(self, contents=''):
        self.contents = contents

    def __delitem__(self, key):
        if isinstance(key, slice):
            start = 0 if key.start is None else key.start
            stop = len(self.contents) if key.stop is None else key.stop
            if start < 0:
                start = len(self.contents)+start
            if stop < 0:
                stop = len(self.contents)-1-(stop+1)
            self.contents = self.contents[:start] + self.contents[stop:]
        elif isinstance(key, int):
            offset = len(self.contents)-1-(key+1) if key < 0 else key
            self.contents = self.contents[:offset] + self.contents[offset+1:]
        else:
            raise TypeError(f'text indices must be integers')

    def insert_at(self, offset, chunk):
        if isinstance(chunk, Text):
            self.contents = self.contents[:offset] + chunk.contents + self.contents[offset:]
        elif isinstance(chunk, str):
            self.contents = self.contents[:offset] + chunk + self.contents[offset:]
        else:
            raise TypeError(f'{chunk} must be of type Text or str')

    def __bool__(self):
        return len(self.contents) == 0

    def __str__(self):
        return self.contents

    def __getitem__(self, key):
        return self.contents[key]

    def __iter__(self):
        return iter(self.contents)

    def __len__(self):
        return len(self.contents)

    def __add__(self, chunk):
        if isinstance(chunk, Text):
            self.contents += chunk.contents
        elif isinstance(chunk, str):
            self.contents += chunk
        else:
            raise TypeError(f'cannot add {chunk} to text')
        return self

def is_blank(ch):
    return ch == ' ' or ch == '\t'

def indent(text, indentation, until_prev_line_blank=True, start=0):
    correct = 0
    for i in range(start, len(text)):
        ch = text[i + correct]
        if ch == '\n':
            until_prev_line_blank = True
        elif until_prev_line_blank and not is_blank(ch):
            until_prev_line_blank = False
            text.insert_at(i + correct, indentation)
            correct += len(indentation)

def get_indentation(text, until_prev_line_blank=True, start=0):
    min_indent = None
    curr_indent = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '\n':
            if not until_prev_line_blank and (curr_indent is None or curr_indent < min_indent):
                min_indent = curr_indent
            until_prev_line_blank = True
            curr_indent = 0
        elif until_prev_line_blank:
            if is_blank(ch):
                curr_indent += 1
        else:
            until_prev_line_blank = False
    if min_indent is None:
        min_indent = 0
    return min_indent

def dedent(text, until_prev_line_blank=True, indentation=None, start=0):
    if indentation is None:
        indentation = get_indentation(text, until_prev_line_blank=until_prev_line_blank, start=start)
    curr_indent = 0
    i = start
    prev_line_offset = 0
    while i < len(text):
        ch = text[i]
        if ch == '\n':
            to_remove = min(curr_indent, indentation)
            del text[prev_line_offset:prev_line_offset+to_remove]
            i -= to_remove
            until_prev_line_blank = True
            prev_line_offset = i+1
            curr_indent = 0
        elif is_blank(ch):
            if until_prev_line_blank:
                curr_indent += 1
        else:
            if until_prev_line_blank:
                until_prev_line_blank = False
        i += 1
    to_remove = min(curr_indent, indentation)
    del text[prev_line_offset:prev_line_offset+to_remove]
    i -= to_remove
