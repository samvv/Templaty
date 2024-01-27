
import sys
from .lines import render, insert_after, rfind, size, Line

def test_size():
    lines = [
        Line('foo', end=False),
        Line('bar', end=True),
        Line('bax', end=False)
    ]
    assert(size(lines) == 10)

def test_insert_after_start():
    lines = [
        Line('foo', end=False),
        Line('bar', end=True),
        Line('bax', end=False)
    ]
    insert_after(lines, 0, [ Line('hello') ])
    assert(render(lines) == 'hello\nfoobar\nbax')

def test_insert_after_mid_of_line():
    lines = [
        Line('foo', end=False),
        Line('bar', end=True),
        Line('bax', end=False)
    ]
    insert_after(lines, 2, [ Line('hello') ])
    assert(render(lines) == 'fohello\nobar\nbax')

def test_insert_after_end():
    lines = [
        Line('foo', end=False),
        Line('bar', end=True),
        Line('bax', end=False)
    ]
    insert_after(lines, 10, [ Line('hello') ])
    assert(render(lines) == 'foobar\nbaxhello\n')

def test_rfind():
    lines = [
        Line('foo', end=False),
        Line('bar', end=True),
        Line('bax', end=False)
    ]
    assert(rfind(lines, lambda ch: ch == 'a') == 8)
    assert(rfind(lines, lambda ch: ch == 'f') == 0)
    assert(rfind(lines, lambda ch: ch == 'o') == 2)

def test_rfind_newline():
    lines = [
        Line('foo', end=False),
        Line('bar', end=True),
        Line('baxaa', end=False)
    ]
    assert(rfind(lines, lambda ch: ch == '\n') == 6)

