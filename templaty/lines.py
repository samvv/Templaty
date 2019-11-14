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


from .util import is_blank, peek, peekable


class Line:


    def __init__(self, text, join_with_next=False, indent_override=None):
        self.indent_override = indent_override
        self.join_with_next = join_with_next
        self.text = text


    def __str__(self):
        out = self.text
        if self.indent_override is not None:
            i = 0
            while i < len(out) and is_blank(out[i]):
                i += 1
            if i > self.indent_override:
                out = out[i - self.indent_override:]
            else:
                out = ' ' * (self.indent_override - i) + out
        if not self.join_with_next:
            out += '\n'
        return out


    def clone(self):
        return Line(self.text, self.join_with_next, self.indent_override)


    def __getitem__(self, key):
        if isinstance(key, slice):
            return Line(self.text[key], self.join_with_next, self.indent_override)
        else:
            return self.text[i]


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


class Lines:


    def __init__(self, lines=[]):
        self._lines = list(lines)


    def __str__(self):
        out = ''
        for line in self._lines:
            out += str(line)
        return out


    def __iter__(self):
        return iter(self._lines)


    def clone(self):
        return Lines(line.clone() for line in self._lines)


    def __iadd__(self, other):
        self._lines.extend(other._lines)
        return self


    def __add__(self, other):
        return Lines(self._lines + other._lines)


    def __len__(self, join_with_prev=False):
        return sum(len(line) for line in self._lines)


    def __getitem__(self, item):

        new_lines = []

        if isinstance(item, int):
            raise NotImplementedError("getting by index is not yet implemented")

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

            if end_offset < 0:
                text_length = len(self)
                if start_offset is None:
                    start_offset = text_length + end_offset
                end_offset = text_length

            j = start_offset
            total_length = end_offset - start_offset

            if total_length < 0:
                raise IndexError("start offset goes beyond end offset")

            line_iter = iter(self._lines)

            for line in line_iter:
                if j < len(line):
                    can_be_added = len(line) - j
                    if j == 0 and total_length >= can_be_added:
                        new_lines.append(line)
                        total_length -= can_be_added
                    else:
                        length = min(total_length, can_be_added)
                        line_part = line[j:j+length]
                        total_length -= length
                        new_lines.append(line_part)
                    break
                else:
                    j -= len(line)

            for line in line_iter:
                can_be_added = len(line)
                if total_length <= 0:
                    break
                elif total_length >= can_be_added:
                    new_lines.append(line)
                    total_length -= can_be_added
                else:
                    length = min(total_length, can_be_added)
                    line_part = line[j:j+length]
                    total_length -= length
                    new_lines.append(line_part)
                    break

        else:
            raise TypeError(f"item {item} must be a slice or a number")

        return Lines(new_lines)


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


    def indent(self, indentation='  ', at_blank_line=True, join_with_prev=False):
        for line in self._lines:
            if at_blank_line:
                for ch in line.text:
                    if not is_blank(ch):
                        at_blank_line = False
                        line.prepend(indentation)
                        break
            if not line.join_with_next:
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
            min_indent = curr_indent
        return min_indent

    def dedent(self, at_blank_line=True, join_with_prev=False):
        min_indent = self.get_indentation(at_blank_line=at_blank_line)
        for line in self._lines:
            if not join_with_prev:
                del line[0:min_indent]
            join_with_prev = line.join_with_next


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
    return Lines(lines)

#  def substring(lines, start_offset, end_offset):
#      for line in get_prefix(lines, start_offset): pass
#      for line in get_prefix(lines, end_offset - start_offset): yield line

#  def substring(lines, start_offset, end_offset):
#  
#      if end_offset is None:
#          j = 0
#          while True:
#              try:
#                  line = next(lines)
#              except StopIteration:
#                  return # or raise an error
#              if j < len(line):
#                  line_part = line[j:]
#                  line_part.join_with_next = True
#                  yield line_part
#                  break
#              else:
#                  j -= len(line)
#                  yield line
#          return
#  
#      if end_offset < 0:
#          line_list = list(lines)
#          text_length = get_length(line_list)
#          lines = iter(line_list)
#          if start_offset is None:
#              start_offset = text_length + end_offset
#          end_offset = text_length
#  
#      j = start_offset
#      total_length = end_offset - start_offset
#  
#      if total_length < 0:
#          raise IndexError("the range to add is invalid")
#  
#      while True:
#          try:
#              line = next(lines)
#          except StopIteration:
#              return # or raise an error
#          if j < len(line):
#              can_be_yielded = len(line) - j
#              if j == 0 and total_length >= can_be_yielded:
#                  yield line
#                  total_length -= can_be_yielded
#              else:
#                  length = min(total_length, len(line.text) - j)
#                  line_part = line[j:j+length]
#                  total_length -= length
#                  if line.join_with_next and total_length == 0:
#                      line_part.join_with_next = False
#                      yield line_part
#                      return
#                  yield line_part
#              j = 0
#              break
#          else:
#              j -= len(line)
#  
#      while True:
#          try:
#              line = next(lines)
#          except StopIteration:
#              break # or raise an error
#          can_be_yielded = len(line)
#          if total_length <= 0:
#              break
#          elif j == 0 and total_length >= can_be_yielded:
#              yield line
#              total_length -= can_be_yielded
#          else:
#              length = min(total_length, len(line.text) - j)
#              line_part = line[j:j+length]
#              total_length -= length
#              if line.join_with_next and total_length == 0:
#                  line_part.join_with_next = False
#                  yield line_part
#                  return
#              yield line_part
#              j = 0

#  def remove_slice(lines, start_offset, end_offset):
#      assert(start_offset >= 0 and end_offset >= 0)
#      for line in get_prefix(lines, start_offset): yield line
#      for line in get_prefix(lines, end_offset - start_offset): pass
#      for line in lines: yield line

#  def remove_slice(lines, start_offset, end_offset):
#  
#      if end_offset < 0:
#          line_list = list(lines)
#          text_length = get_length(line_list)
#          lines = iter(line_list)
#          if start_offset is None:
#              start_offset = text_length + end_offset
#          end_offset = text_length
#  
#      i = 0
#      j = start_offset
#      total_to_remove = end_offset - start_offset
#  
#      if total_to_remove < 0:
#          raise IndexError("the range to remove is invalid")
#  
#      while True:
#          try:
#              line = next(lines)
#          except StopIteration:
#              return # or raise an error
#          if j < len(line):
#              can_be_removed = len(line) - j
#              if j == 0 and total_to_remove >= can_be_removed:
#                  total_to_remove -= can_be_removed
#              else:
#                  to_remove = min(total_to_remove, len(line.text) - j)
#                  line_part = line.remove_slice(j, j+to_remove)
#                  total_to_remove -= to_remove
#                  if not line.join_with_next and total_to_remove > 0:
#                      line_part.join_with_next = True
#                      total_to_remove -= 1
#                  yield line_part
#              j = 0
#              break
#          else:
#              j -= len(line)
#              yield line
#          i += 1
#  
#      while True:
#          try:
#              line = next(lines)
#          except StopIteration:
#              break # or raise an error
#          can_be_removed = len(line)
#          if total_to_remove <= 0:
#              yield line
#          elif j == 0 and total_to_remove >= can_be_removed:
#              total_to_remove -= can_be_removed
#          else:
#              to_remove = min(total_to_remove, len(line.text) - j)
#              line_part = line.remove_slice(j, j+to_remove)
#              total_to_remove -= to_remove
#              if not line.join_with_next and total_to_remove > 0:
#                  line_part.join_with_next = True
#                  total_to_remove -= 1
#              yield line_part
#              j = 0
