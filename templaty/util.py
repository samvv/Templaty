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

def is_empty(text):
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

def breadthfirst(root, expand):
    queue = [root]
    while len(queue) > 0:
        node = queue.pop(0)
        yield node
        for node in reversed(list(expand(node))):
            queue.append(node)

def preorder(root, expand):
    stack = [root]
    while len(stack) > 0:
        node = stack.pop()
        yield node
        for node in expand(node):
            stack.append(node)

def postorder(root, expand):
    stack_1 = [root]
    stack_2 = []
    while len(stack_1) > 0:
        node = stack_1.pop()
        stack_2.append(node)
        for child in reversed(list(expand(node))):
            stack_1.append(child)
    for node in reversed(stack_2):
        yield node

def set_all_parents(node, parent=None):
    node.parent = parent
    for child in gast.iter_child_nodes(node):
        set_all_parents(child, node)

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

import typing

def is_list_type(ty):
    return hasattr(ty, '__origin__') and ty.__origin__ == list

def is_union_type(ty):
    return hasattr(ty, '__origin__') and ty.__origin__ == typing.Union

def is_none_type(ty):
    return ty == type(None)

def flatten_union_type(ty):
    if is_union_type(ty):
        return ((el2_ty for el2_ty in flatten_union_type(el_ty)) for el_ty in ty.__args__)
    else:
        return [ty]

def is_type_optional(ty):
    return any(is_none_type(el_ty) for el_ty in flatten_union_type(ty))

def get_element_type(ty):
    if is_list_type(ty):
        return ty.__args__[0]
    elif is_union_type(ty):
        return next(get_element_type(el_ty) for el_ty in flatten_union_type(ty) if not is_none_type(el_ty))
    else:
        return ty

def is_special_type(ty):
    return ty == typing.Any or is_none_type(ty)

def get_index_type(ty):
    if is_list_type(ty):
        return int
    else:
        return None

def preorder(node):
    stack = [node]
    while len(stack) > 0:
        front = stack.pop()
        yield front
        for node in front.get_child_nodes():
            stack.append(node)

class BaseNode:

    def __init__(self, *args, **kwargs):
        self.parent = None
        fields = self.__dict__['_fields'] = dict()
        i = 0
        for name, ty in self.__class__.__annotations__.items():
            if name in kwargs:
                value = kwargs[name]
            else:
                value = args[i]
                i += 1
            fields[name] = value
        for name, ty in self.__class__.__annotations__.items():
            if not name in fields:
                if is_list_type(ty):
                    fields[name] = []
                elif is_type_optional(ty):
                    fields[name] = None
                else:
                    raise TypeError(f"field '{name}' is required but did not receive a value")

    def get_field_names(self):
        return iter(self.__class__.__annotations__.keys())

    def get_child_nodes(self):
        for name, value in self.__dict__['_fields'].items():
            if value is not None:
                ty = get_element_type(self.__class__.__annotations__[name])
                if not is_special_type(ty) and issubclass(ty, BaseNode):
                    if isinstance(value, list):
                        for el in value:
                            yield el
                    else:
                        yield value

    def get_field_items(self):
        for name, value in self.__dict__['_fields'].items():
            if value is not None:
                if isinstance(value, list):
                    for el in value:
                        yield (name, el)
                else:
                    yield (name, value)

    def __getattr__(self, name):
        fields = self.__dict__['_fields']
        if name in fields:
            return fields[name]
        if name in self.__dict__:
            return self.__dict__[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in self.__class__.__annotations__:
            self.__dict__['_fields'][name] = value
        else:
            self.__dict__[name] = value

