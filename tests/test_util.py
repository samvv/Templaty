
import unittest

from templaty.util import *

class TestGetIndentation(unittest.TestCase):

    def test_no_newlines(self):
        self.assertEqual(get_indentation("this is just one line of text"), 0)
        self.assertEqual(get_indentation("  foo"), 2)
        self.assertEqual(get_indentation("\tfoo"), 1)

    def test_preceeding_newline(self):
        self.assertEqual(get_indentation("\n\nthis is just one line of text"), 0)
        self.assertEqual(get_indentation("\n  foo"), 2)
        self.assertEqual(get_indentation("\n  foo"), 2)
        self.assertEqual(get_indentation("\n\nthis is just one line of text\n"), 0)
        self.assertEqual(get_indentation("\n\tfoo\n"), 1)
        self.assertEqual(get_indentation("\n\tfoo\b"), 1)

    def test_trailing_newline(self):
        self.assertEqual(get_indentation("this is just one line of text\n"), 0)
        self.assertEqual(get_indentation("  foo\n"), 2)
        self.assertEqual(get_indentation("\tfoo\n"), 1)

    def test_mutliline(self):
        self.assertEqual(get_indentation("  foo\n  bar\n  baz"), 2)
        self.assertEqual(get_indentation("  foo\n  bar\n  baz\n"), 2)
        self.assertEqual(get_indentation("\tfoo\n\tbar\n\tbaz"), 1)

    def test_nested_multiline(self):
        self.assertEqual(get_indentation("  foo\n    bar\n  baz\n"), 2)
        self.assertEqual(get_indentation("  foo\n    bar\n  baz"), 2)
        self.assertEqual(get_indentation("    foo\n  bar\n    baz\n"), 2)
        self.assertEqual(get_indentation("    foo\n  bar\n    baz"), 2)

#  class TestDedent(unittest.TestCase):
#  
#      #  def test_empty_line(self):
#      #      k1, t1 = indent('\n\n\n')
#      #      self.assertEqual(t1, '\n\n\n')
#      #      self.assertEqual(k1, 0)
#      #      k2, t2 = indent('  \n  \n  \n'), '  \n  \n  \n')
#      #      self.assertEqual(k2, 0)
#  
#      def test_multiline(self):
#          self.assertEqual(dedent('  foo\n  bar\n  baz\n') 'foo\nbar\nbaz\n')
#  
#  class TestIndent(unittest.TestCase):
#  
#      def test_empty_line(self):
#          self.assertEqual(indent('\n\n\n'), '\n\n\n')
#          self.assertEqual(indent('  \n  \n  \n'), '  \n  \n  \n')
#  
#      def test_multiline(self):
#          self.assertEqual(indent('foo\nbar\nbaz\n'), '  foo\n  bar\n  baz\n')
#          self.assertEqual(indent('  foo\n  bar\n  baz\n'), '    foo\n    bar\n    baz\n')
#  
#      def test_mixed(self):
#          self.assertEqual(indent('\n\nfoo\n  bar\nbaz\n\n'), '\n\n  foo\n    bar\n  baz\n\n')
#  
