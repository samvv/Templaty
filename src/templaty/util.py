
from collections.abc import Iterable
import re
from typing import Protocol

class ToString(Protocol):
    def __str__(self) -> str: ...

def enum_or(raw_elements: Iterable[ToString]) -> str:
    elements = list(raw_elements)
    if len(elements) == 1:
        return str(elements[0])
    else:
        return ', '.join(str(el) for el in elements[0:-1]) + ' or ' + str(elements[-1])

def is_blank(text: str) -> bool:
    for ch in text:
        if not ch == ' ' and not ch == '\t':
            return False
    return True

def is_whitespace(text: str) -> bool:
    for ch in text:
        if not is_blank(ch) and not ch == '\n':
            return False
    return True

def starts_with_newline(text: str) -> bool:
    for ch in text:
        if ch == '\n':
            return True
        if ch == ' ' or ch == '\t' or ch == '\r':
            continue
        break
    return False

def ends_with_newline(text: str) -> bool:
    for ch in reversed(text):
        if ch == '\n':
            return True
        if ch == ' ' or ch == '\t' or ch == '\r':
            continue
        break
    return False

def remove_last_newline(text: str) -> str:
    i = 0
    while i < len(text):
        ch = text[len(text)-i]
        if ch == '\n':
            i -= 1
            break
        if not is_blank(ch):
            return text
        i -= 1
    while i < len(text) and is_blank(text[len(text)-i]):
        i += 1
    return text[0:i+1]

def dedent(text: str, at_blank_line=True) -> str:
    indent_length = get_indentation(text, at_blank_line)
    curr_removed = 0
    out = ''
    for ch in text:
        if ch == '\n':
            at_blank_line = True
        elif is_blank(ch):
            if curr_removed < indent_length:
                curr_removed += 1
                continue
        else:
            curr_removed = 0
        out += ch
    return out

def indent(text: str, indentation='  ', at_blank_line=True) -> str:
    out = ''
    for ch in text:
        if not at_blank_line:
            at_blank_line = ch == '\n'
        elif ch == '\n':
            at_blank_line = True
        elif not is_blank(ch):
            at_blank_line = False
            out += indentation
        out += ch
    return out

def is_last_line_blank(text: str) -> bool:
    for ch in reversed(text):
        if ch == '\n':
            break
        elif not is_blank(ch):
            return False
    return True

def get_indentation(text: str, at_blank_line=True, default_indent=0):
    min_indent = None
    curr_indent = 0
    for ch in text:
        if at_blank_line:
            if is_blank(ch):
                curr_indent += 1
                continue
            at_blank_line = ch == '\n'
            if not at_blank_line and (min_indent is None or curr_indent < min_indent):
                min_indent = curr_indent
        else:
            if ch == '\n':
                at_blank_line = True
                curr_indent = 0
    if min_indent is None:
        min_indent = default_indent if at_blank_line else curr_indent 
    return min_indent

def to_snake_case(name: str) -> str:
    if '-' in name:
        return name.replace('-', '_')
    else:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_camel_case(name: str, first_char_lowercase=False) -> str:
    result = re.sub(r'[-_]', '', name.title())
    return result[0].lower() + result[1:] if first_char_lowercase else result

SPECIAL_CHARS = {
        '\x09': '\\t',
        '\x0D': '\\r',
        '\x0A': '\\n',
        '\x5C': '\\',
        }

def escape(text: str) -> str:
    out = ''
    for ch in text:
        if ch in SPECIAL_CHARS:
            out += SPECIAL_CHARS[ch]
        elif ch.isprintable():
        #  elif ord(ch) >= 0x20 and ord(ch) <= 0x7E:
            out += ch
        else:
            code = ord(ch)
            out += f"\\x{code:02X}" if code <= 0x7F else f'\\u{code:04X}'
    return out

