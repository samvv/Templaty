
from .evaluator import indent, dedent, get_indentation

# def test_text_del_int():
#     t0 = Text('foobar')
#     del t0[0]
#     assert(str(t0) == 'oobar')
#     del t0[2]
#     assert(str(t0) == 'ooar')
#     del t0[-1]
#     assert(str(t0) == 'ooa')
#     del t0[1:1]
#     assert(str(t0) == 'ooa')

# def test_text_del_slice():
#     t0 = Text('foobarbaz')
#     del t0[3:6]
#     assert(str(t0) == 'foobaz')
#     del t0[4:-1]
#     assert(str(t0) == 'foobz')
#     del t0[:]
#     assert(str(t0) == '')

def test_indent():
    t0 = 'foo\nbar\nbaz\n'
    assert(indent(t0, '  ') == '  foo\n  bar\n  baz\n')

def test_dedent():
    t0 = '    \n  \n \n  foo\n  \nbaz\nbar\n\n'
    assert(dedent(t0, indentation=2) == '  \n\n\nfoo\n\nbaz\nbar\n\n')