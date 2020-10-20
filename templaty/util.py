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

def enum_or(raw_elements):
    elements = list(raw_elements)
    if len(elements) == 1:
        return str(elements[0])
    else:
        return ', '.join(str(el) for el in elements[0:-1]) + ' or ' + str(elements[-1])

def is_blank(text):
    for ch in text:
        if not ch == ' ' and not ch == '\t':
            return False
    return True

def is_whitespace(text):
    for ch in text:
        if not is_blank(ch) and not ch == '\n':
            return False
    return True

def starts_with_newline(text):
    for ch in text:
        if ch == '\n':
            return True
        if ch == ' ' or ch == '\t' or ch == '\r':
            continue
        break
    return False

def ends_with_newline(text):
    for ch in reversed(text):
        if ch == '\n':
            return True
        if ch == ' ' or ch == '\t' or ch == '\r':
            continue
        break
    return False

def remove_last_newline(text):
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

def dedent(text, at_blank_line=True):
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

def indent(text, indentation='  ', at_blank_line=True):
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

def is_last_line_blank(text):
    for ch in reversed(text):
        if ch == '\n':
            break
        elif not is_blank(ch):
            return False
    return True

def get_indentation(text, at_blank_line=True, default_indent=0):
    min_indent = None
    curr_indent = 0
    for ch in text:
        if not at_blank_line:
            if ch == '\n':
                at_blank_line = True
                curr_indent = 0
        else:
            if is_blank(ch):
                curr_indent += 1
                continue
            at_blank_line = ch == '\n'
            if not at_blank_line and (min_indent is None or curr_indent < min_indent):
                min_indent = curr_indent
    if min_indent is None:
        min_indent = default_indent
    return min_indent

def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

SPECIAL_CHARS = {
        '\x09': '\\t',
        '\x0D': '\\r',
        '\x0A': '\\n',
        '\x5C': '\\',
        }

def escape(text):
    out = ''
    for ch in text:
        if ch in SPECIAL_CHARS:
            out += SPECIAL_CHARS[ch]
        elif ch.isprintable():
        #  elif ord(ch) >= 0x20 and ord(ch) <= 0x7E:
            out += ch
        elif ord(ch) <= 0x7F:
            out += "\\x{:02X}".format(ord(ch))
        else:
            out += '\\u{:04X}'.format(ord(ch))
    return out
