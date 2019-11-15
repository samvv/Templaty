
from unittest import TestCase

from templaty.lines import *

class TestRemoveSlice(TestCase):

    def test_joined_lines(self):
        t = Lines([Line('foo', True), Line('bar', True), Line('bax', True)])
        t1 = t.clone()
        del t1[0:3]
        self.assertEqual(str(t1), 'barbax')
        t2 = t.clone()
        del t2[0:4]
        self.assertEqual(str(t2), 'arbax')
        t3 = t.clone()
        del t3[0:5]
        self.assertEqual(str(t3), 'rbax')
        t4 = t.clone()
        del t4[0:6]
        self.assertEqual(str(t4), 'bax')
        t5 = t.clone()
        del t5[0:7]
        self.assertEqual(str(t5), 'ax')
        t6 = t.clone()
        del t6[0:8]
        self.assertEqual(str(t6), 'x')
        t7 = t.clone()
        del t7[0:9]
        self.assertEqual(str(t7), '')
        t8 = t.clone()
        del t8[0:10]
        self.assertEqual(str(t8), '')
        t9 = t.clone()
        del t9[0:11]
        self.assertEqual(str(t9), '')
        t10 = t.clone()
        del t10[0:12]
        self.assertEqual(str(t10), '')


    def test_regular_lines(self):
        t = Lines([Line('foo'), Line('bar'), Line('bax')])
        t1 = t.clone()
        del t1[0:3]
        self.assertEqual(str(t1), '\nbar\nbax\n')
        t2 = t.clone()
        del t2[0:4]
        self.assertEqual(str(t2), 'bar\nbax\n')
        t3 = t.clone()
        del t3[0:5]
        self.assertEqual(str(t3), 'ar\nbax\n')
        t4 = t.clone()
        del t4[0:6]
        self.assertEqual(str(t4), 'r\nbax\n')
        t5 = t.clone()
        del t5[0:7]
        self.assertEqual(str(t5), '\nbax\n')
        t6 = t.clone()
        del t6[0:8]
        self.assertEqual(str(t6), 'bax\n')
        t7 = t.clone()
        del t7[0:9]
        self.assertEqual(str(t7), 'ax\n')
        t8 = t.clone()
        del t8[0:10]
        self.assertEqual(str(t8), 'x\n')
        t9 = t.clone()
        del t9[0:11]
        self.assertEqual(str(t9), '\n')
        t10 = t.clone()
        del t10[0:12]
        self.assertEqual(str(t10), '')


    def test_before_newline(self):
        t = Lines([Line('foo'), Line('bar'), Line('bax')])
        t1 = t.clone()
        del t1[3:3]
        self.assertEqual(str(t1), 'foo\nbar\nbax\n')
        t2 = t.clone()
        del t2[3:4]
        self.assertEqual(str(t2), 'foobar\nbax\n')
        t3 = t.clone()
        del t3[3:5]
        self.assertEqual(str(t3), 'fooar\nbax\n')
        t4 = t.clone()
        del t4[3:6]
        self.assertEqual(str(t4), 'foor\nbax\n')
        t5 = t.clone()
        del t5[3:7]
        self.assertEqual(str(t5), 'foo\nbax\n')
        t6 = t.clone()
        del t6[3:8]
        self.assertEqual(str(t6), 'foobax\n')
        t7 = t.clone()
        del t7[3:9]
        self.assertEqual(str(t7), 'fooax\n')
        t8 = t.clone()
        del t8[3:10]
        self.assertEqual(str(t8), 'foox\n')
        t9 = t.clone()
        del t9[3:11]
        self.assertEqual(str(t9), 'foo\n')
        t10 = t.clone()
        del t10[3:12]
        self.assertEqual(str(t10), 'foo')


    def test_after_newline(self):
        t = Lines([Line('foo'), Line('bar'), Line('bax')])
        t1 = t.clone()
        del t1[4:4]
        self.assertEqual(str(t1), 'foo\nbar\nbax\n')
        t2 = t.clone()
        del t2[4:5]
        self.assertEqual(str(t2), 'foo\nar\nbax\n')
        t3 = t.clone()
        del t3[4:6]
        self.assertEqual(str(t3), 'foo\nr\nbax\n')
        t4 = t.clone()
        del t4[4:7]
        self.assertEqual(str(t4), 'foo\n\nbax\n')
        t5 = t.clone()
        del t5[4:8]
        self.assertEqual(str(t5), 'foo\nbax\n')
        t6 = t.clone()
        del t6[4:9]
        self.assertEqual(str(t6), 'foo\nax\n')
        t7 = t.clone()
        del t7[4:10]
        self.assertEqual(str(t7), 'foo\nx\n')
        t8 = t.clone()
        del t8[4:11]
        self.assertEqual(str(t8), 'foo\n\n')
        t9 = t.clone()
        del t9[4:12]
        self.assertEqual(str(t9), 'foo\n')
        t10 = t.clone()
        del t10[4:13]
        self.assertEqual(str(t10), 'foo\n')


    def test_after_newline(self):
        t = Lines([Line('foo'), Line('bar'), Line('bax')])
        t1 = t.clone()
        del t1[6:6]
        self.assertEqual(str(t1), 'foo\nbar\nbax\n')
        t2 = t.clone()
        del t2[6:7]
        self.assertEqual(str(t2), 'foo\nba\nbax\n')
        t3 = t.clone()
        del t3[6:8]
        self.assertEqual(str(t3), 'foo\nbabax\n')
        t4 = t.clone()
        del t4[6:9]
        self.assertEqual(str(t4), 'foo\nbaax\n')
        t5 = t.clone()
        del t5[6:10]
        self.assertEqual(str(t5), 'foo\nbax\n')
        t6 = t.clone()
        del t6[6:11]
        self.assertEqual(str(t6), 'foo\nba\n')
        t7 = t.clone()
        del t7[6:12]
        self.assertEqual(str(t7), 'foo\nba')
        t8 = t.clone()
        del t8[6:13]
        self.assertEqual(str(t8), 'foo\nba')

class TestInsertAt(TestCase):

    def test_no_newline(self):
        t1 = Lines([Line('foo', True), Line('bar', True), Line('bax', True)])
        t1.insert_at(0, Lines([Line('tes', True)]))
        self.assertEqual(str(t1), 'tesfoobarbax')
        t2 = Lines([Line('foo', True), Line('bar', True), Line('bax', True)])
        t2.insert_at(1, Lines([Line('bla', True)]))
        self.assertEqual(str(t2), 'fblaoobarbax')
        t3 = Lines([Line('foo', True), Line('bar', True), Line('bax', True)])
        t3.insert_at(2, Lines([Line('bla', True)]))
        self.assertEqual(str(t3), 'foblaobarbax')
        t2 = Lines([Line('foo', True), Line('bar', True), Line('bax', True)])
        t2.insert_at(3, Lines([Line('bla', True)]))
        self.assertEqual(str(t2), 'fooblabarbax')

    def test_insert_end(self):
        t1 = Lines([Line('foo', True), Line('bar', True), Line('bax', True)])
        t1.insert_at(9, Lines([Line('tes', True)]))
        self.assertEqual(str(t1), 'foobarbaxtes')
        t2 = Lines([Line('foo', True), Line('bar', True), Line('bax', True)])
        t2.insert_at(8, Lines([Line('tes', True)]))
        self.assertEqual(str(t2), 'foobarbatesx')
        t2 = Lines([Line('foo'), Line('bar'), Line('bax')])
        t2.insert_at(12, Lines([Line('tes', True)]))
        self.assertEqual(str(t2), 'foo\nbar\nbax\ntes')

    def test_newline(self):
        t1 = Lines([Line('foo'), Line('bar'), Line('bax', True)])
        t1.insert_at(0, Lines([Line('tes', True)]))
        self.assertEqual(str(t1), 'tesfoo\nbar\nbax')
        t2 = Lines([Line('foo'), Line('bar'), Line('bax', True)])
        t2.insert_at(1, Lines([Line('bla', True)]))
        self.assertEqual(str(t2), 'fblaoo\nbar\nbax')
        t3 = Lines([Line('foo'), Line('bar'), Line('bax', True)])
        t3.insert_at(2, Lines([Line('bla', True)]))
        self.assertEqual(str(t3), 'foblao\nbar\nbax')
        t2 = Lines([Line('foo'), Line('bar'), Line('bax', True)])
        t2.insert_at(3, Lines([Line('bla', True)]))
        self.assertEqual(str(t2), 'foobla\nbar\nbax')
        t3 = Lines([Line('foo'), Line('bar'), Line('bax', True)])
        t3.insert_at(4, Lines([Line('bla', True)]))
        self.assertEqual(str(t3), 'foo\nblabar\nbax')

class TestIndent(TestCase):

    def test_simple_multiline(self):
        t1 = Lines([Line('foo'), Line('bar'), Line('bax', True)])
        t1.indent('  ')
        self.assertEqual(str(t1), '  foo\n  bar\n  bax')
        t2 = Lines([Line('0'), Line('1'), Line('2')])
        t2.indent('  ')
        self.assertEqual(str(t2), '  0\n  1\n  2\n')

