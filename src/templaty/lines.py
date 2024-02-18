
from typing import Callable

class Line:

    def __init__(self, text: str, indent_override: int | None = None, end = True) -> None:
        self.text = text
        self.end = end
        self.indent_override = indent_override

    def __len__(self) -> int:
        count = len(self.text)
        if self.end:
            count += 1
        return count

Lines = list[Line]

def render(lines: Lines) -> str:
    out = ''
    for line in lines:
        out += line.text
        if line.end:
            out += '\n'
    return out

def size(lines: Lines) -> int:
    count = 0
    for line in lines:
        count += len(line)
    return count

def rfind(lines: Lines, pred: Callable[[str], bool]) -> int:
    line_index = len(lines)
    skipped = 0
    while line_index > 0:
        line = lines[line_index-1]
        k = len(line.text)
        if line.end and pred('\n'):
            return size(lines) - skipped - 1
        while k > 0:
            ch = line.text[k-1]
            if pred(ch):
                skipped_in_line = len(line.text) - k
                return size(lines) - skipped - skipped_in_line - (1 if line.end else 0)
            k -= 1
        skipped += len(line)
        line_index -= 1
    return -1

def insert_after(lines: Lines, offset: int, to_insert: Lines) -> None:
    line_index = 0
    k = offset
    while line_index < len(lines):
        line = lines[line_index]
        if k < len(line):
            del lines[line_index]
            lines.insert(line_index, Line(line.text[0:k], end=False))
            line_index += 1
            for line_to_insert in to_insert:
                lines.insert(line_index, line_to_insert)
                line_index += 1
            lines.insert(line_index, Line(line.text[k:], end=line.end))
            return
        k -= len(line)
        line_index += 1
    if k == 0:
        lines.extend(to_insert)
        return
    raise RuntimeError(f'offset {offset} out of range')

