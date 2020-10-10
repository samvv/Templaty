
from templaty.util import *

def test_get_indentation_no_newlines():
    assert(get_indentation("this is just one line of text") == 0)
    assert(get_indentation("  foo") == 2)
    assert(get_indentation("\tfoo") == 1)

def test_get_indentation_preceeding_newline():
    assert(get_indentation("\n\nthis is just one line of text") == 0)
    assert(get_indentation("\n  foo") == 2)
    assert(get_indentation("\n  foo") == 2)
    assert(get_indentation("\n\nthis is just one line of text\n") == 0)
    assert(get_indentation("\n\tfoo\n") == 1)
    assert(get_indentation("\n\tfoo\b") == 1)

def test_get_indentation_trailing_newline():
    assert(get_indentation("this is just one line of text\n") == 0)
    assert(get_indentation("  foo\n") == 2)
    assert(get_indentation("\tfoo\n") == 1)

def test_get_indentation_mutliline():
    assert(get_indentation("  foo\n  bar\n  baz") == 2)
    assert(get_indentation("  foo\n  bar\n  baz\n") == 2)
    assert(get_indentation("\tfoo\n\tbar\n\tbaz") == 1)

def test_get_indentation_nested_multiline():
    assert(get_indentation("  foo\n    bar\n  baz\n") == 2)
    assert(get_indentation("  foo\n    bar\n  baz") == 2)
    assert(get_indentation("    foo\n  bar\n    baz\n") == 2)
    assert(get_indentation("    foo\n  bar\n    baz") == 2)

#  class TestDedent(unittest.TestCase):
#  
#      #  def test_empty_line():
#      #      k1, t1 = indent('\n\n\n')
#      #      assert(t1, '\n\n\n')
#      #      assert(k1, 0)
#      #      k2, t2 = indent('  \n  \n  \n'), '  \n  \n  \n')
#      #      assert(k2, 0)
#  
#      def test_multiline():
#          assert(dedent('  foo\n  bar\n  baz\n') 'foo\nbar\nbaz\n')
#  
#  class TestIndent(unittest.TestCase):
#  
#      def test_empty_line():
#          assert(indent('\n\n\n'), '\n\n\n')
#          assert(indent('  \n  \n  \n'), '  \n  \n  \n')
#  
#      def test_multiline():
#          assert(indent('foo\nbar\nbaz\n'), '  foo\n  bar\n  baz\n')
#          assert(indent('  foo\n  bar\n  baz\n'), '    foo\n    bar\n    baz\n')
#  
#      def test_mixed():
#          assert(indent('\n\nfoo\n  bar\nbaz\n\n'), '\n\n  foo\n    bar\n  baz\n\n')
#  
