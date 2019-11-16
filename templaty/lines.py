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

"""Classes for working with lines of text.

These classes resemble the ordinary string operations, but they were
fine-tuned to work very efficiently on lists of special line objects.
"""


from .util import is_blank


class Line:


    def __init__(self, text, join_with_next=False, indent_override=None):
        self.indent_override = indent_override
        self.join_with_next = join_with_next
        self.text = text


    def __str__(self):
        out = self.text
        if not self.join_with_next:
            out += '\n'
        return out


    def clone(self):
        return Line(self.text, self.join_with_next, self.indent_override)


    def __getitem__(self, index):

        if isinstance(index, int):

            # FIXME probably should return a line object in order
            # to be consistent with the slice API
            if index < len(self.text):
                return self.text[index]
            if index == len(self.text) and not self.join_with_next:
                return '\n'
            raise IndexError('index out of bounds')

        elif isinstance(index, slice):

            result = Line(self.text[index], self.join_with_next, self.indent_override)

            # if we take a slice that does not include the full right half of
            # the line, then join_with_next is set to True so that a
            # hypothetical join() works
            if index.stop is not None and index.stop <= len(self.text):
                result.join_with_next = True

            return result
        else:
            raise NotImplementedError("type is not supported")


    def __delitem__(self, item):
        if isinstance(item, int):
            if item < 0:
                item = item + len(self)
            if item < len(self.text):
                self.text = self.text[0:item] + self.text[0:item+1]
            if item == len(self.text):
                self.join_with_next = True
        elif isinstance(item, slice):
            start_offset = 0 if item.start is None else item.start
            end_offset = len(self) if item.stop is None else item.stop
            assert(0 <= start_offset < len(self))
            assert(0 <= end_offset <= len(self))
            assert(start_offset <= end_offset)
            if end_offset > len(self.text):
                self.join_with_next = True
            self.text = self.text[:start_offset] + self.text[end_offset:]
        else:
            raise TypeError("item must be a slice or an integer")


    def __len__(self):
        length = len(self.text)
        if not self.join_with_next:
            length += 1
        return length


    def prepend(self, prefix):
        self.text = prefix + self.text


def split_lines(text):
    lines = []
    buffered = ''
    for ch in text:
        if ch == '\n':
            lines.append(Line(buffered))
            buffered = ''
        else:
            buffered += ch
    if len(buffered) > 0:
        lines.append(Line(buffered, True))
    return lines


class Lines:


    def __init__(self, lines=[]):
        if isinstance(lines, str):
            lines = split_lines(lines)
        else:
            lines = list(lines)
        self._lines = lines


    def __str__(self):
        out = ''
        for line in self._lines:
            out += str(line)
        return out


    def get_lines(self):
        return iter(self._lines)


    def clone(self):
        return Lines(line.clone() for line in self._lines)


    def __iadd__(self, other):
        self._lines.extend(other._lines)
        return self


    def __add__(self, other):
        return Lines(self._lines + other._lines)


    def __len__(self):
        return sum(len(line) for line in self._lines)


    def get_line(self, index):
        return self._lines[index]


    def __getitem__(self, item):

        if isinstance(item, int):
            for line in self._lines:
                line_length = len(line)
                if item < line_length:
                    return line[item]
                else:
                    item -= line_length
            raise IndexError("lines index out of range")
        else:
            raise NotImplementedError("type is not supported")


    def insert_at(self, offset, lines):
        if len(lines._lines) == 0:
            return
        k = offset
        for i, line in enumerate(self._lines):
            if k < len(line):
                del self._lines[i]
                prefix = line[:k]
                suffix = line[k:]
                if len(prefix) > 0:
                    self._lines.insert(i, prefix)
                    i += 1
                for j, line_2 in enumerate(lines._lines):
                    self._lines.insert(i, line_2)
                    i += 1
                if len(suffix) > 0:
                    self._lines.insert(i, suffix)
                return
            else:
                k -= len(line)
        if k == 0:
            self._lines.extend(lines._lines)
        else:
            raise IndexError(f"index {offset} out of bounds")


    def find(self, pred):
        if isinstance(pred, str):
            expected = pred
            pred = lambda ch: ch == expected
        offset = len(self)
        for line in self._lines:
            for ch in line: 
                if pred(ch):
                    return offset
                else:
                    offset -= 1
        return len(self)

    def __delitem__(self, item):

        if isinstance(item, int):
            raise NotImplementedError("deleting by index is not yet implemented")

        elif isinstance(item, slice):

            start_offset = item.start
            end_offset = item.stop

            if start_offset is None:
                start_offset = 0
            elif start_offset < 0:
                start_offset = len(self) + start_offset

            if end_offset is None:
                end_offset = len(self)
            elif end_offset < 0:
                end_offset = len(self) + end_offset

            i = 0
            j = start_offset
            total_to_remove = end_offset - start_offset

            if total_to_remove < 0:
                raise IndexError("start offset goes beyond end offset")

            while i < len(self._lines):
                line = self._lines[i]
                if j < len(line):
                    can_be_removed = len(line) - j
                    if j == 0 and total_to_remove >= can_be_removed:
                        del self._lines[i]
                        total_to_remove -= can_be_removed
                    else:
                        to_remove = min(total_to_remove, can_be_removed)
                        del line[j:j+to_remove]
                        total_to_remove -= to_remove
                        i += 1
                    break
                else:
                    j -= len(line)
                    i += 1

            while i < len(self._lines):
                line = self._lines[i]
                can_be_removed = len(line)
                if total_to_remove <= 0:
                    break 
                elif total_to_remove >= can_be_removed:
                    del self._lines[i]
                    total_to_remove -= can_be_removed
                else:
                    to_remove = min(total_to_remove, can_be_removed)
                    del line[0:to_remove]
                    total_to_remove -= to_remove
                    break

        else:
            raise TypeError(f"item {item} must be a slice or a number")


    def indent(self, indentation='  ', at_blank_line=True, join_with_prev=False, start=0):
        offset = 0
        for line in self._lines:
            if at_blank_line:
                for i, ch in enumerate(line.text):
                    if not is_blank(ch):
                        at_blank_line = False
                        if (offset + i) >= start:
                            line.prepend(indentation)
                        break
            offset += len(line.text)
            if not line.join_with_next:
                offset += 1
                at_blank_line = True

    def get_indentation(self, at_blank_line=True, default_indent=0):
        min_indent = None
        curr_indent = 0
        for line in self._lines:
            if at_blank_line:
                for ch in line.text:
                    if is_blank(ch):
                        curr_indent += 1
                    elif min_indent is None or curr_indent < min_indent:
                        min_indent = curr_indent
            if not line.join_with_next:
                at_blank_line = True
                curr_indent = 0
        if min_indent is None:
            min_indent = default_indent
        return min_indent

    def dedent(self, at_blank_line=True, min_indent=None):
        if min_indent is None:
            min_indent = self.get_indentation(at_blank_line=at_blank_line)
        for line in self._lines:
            if at_blank_line:
                i = 0
                while i < len(line.text):
                    if not is_blank(line.text[i]):
                        at_blank_line = False
                        break
                    i += 1
                to_remove = min(min_indent, i)
                if to_remove > 0:
                    del line[0:to_remove]
            if not line.join_with_next:
                at_blank_line = True


def apply_indent_override(lines):
    output = ''
    lines = lines._lines
    i = 0

    while i < len(lines):

        indent_override = lines[i].indent_override

        # look ahead to see if this line or the next may contain
        # an indent_override flag
        j = i + 1
        while j < len(lines) and lines[j].join_with_next:
            if lines[j].indent_override is not None:
                indent_override = lines[j].indent_override
                break
            j += 1

        # no indent_override means there is no
        # special processing that has to take place
        if indent_override is None:
            output += str(lines[i])

        else:

            curr_indent_override = indent_override
            k = 0

            while i < len(lines):

                # pass through any characters that
                # are accepted by curr_indent_override
                while k < len(lines[i].text):
                    ch = lines[i].text[k]
                    if curr_indent_override == 0:
                        break
                    elif is_blank(ch):
                        curr_indent_override -= 1
                        output += ch
                        k += 1
                    else:
                        output += ' ' * curr_indent_override
                        break

                # FIXME currently no code requires this
                # if the line was not long enough and the next line might still
                # contain indentation, then now is the time to process it
                #  if curr_indent_override > 0:
                #      i += 1
                #      continue

                # skip any characters that are remaining
                # because they are excess indentation
                while k < len(lines[i].text) and is_blank(lines[i].text[k]):
                    k += 1

                # now the real string is added
                output += lines[i].text[k:]

                # finish off unless we have to append more lines
                if not lines[i].join_with_next:
                    output += '\n'
                    break

                curr_indent_override = indent_override
                i += 1

        i += 1

    return output
