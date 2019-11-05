
import templaty

import unittest

INDENT_TEXT = """
    This text is indented.
    This is just to make sure the indentation remains the same.
"""

class TestEvaluator(unittest.TestCase):

    def test_simple_text(self):
        self.assertEqual(templaty.evaluate("Hello, world!"), "Hello, world!")
        self.assertEqual(templaty.evaluate(b"\xF0\x9F\x90\x80".decode('utf-8')), "🐀")
        self.assertEqual(templaty.evaluate(INDENT_TEXT), INDENT_TEXT)

    def test_simple_for_in_range(self): 
        self.assertEqual(templaty.evaluate("{% for i in range(0, 3) %}(foo){% endfor %}"), "(foo)(foo)(foo)")

    def test_simple_for_in_range_indented_unwrapped(self):
        self.assertEqual(templaty.evaluate("  {% for i in range(0, 3) %}{{i}}\n{% endfor %}"), "  0\n  1\n  2\n")

    def test_simple_for_in_range_indented_wrapped(self):
        self.assertEqual(templaty.evaluate("  {% for i in range(0, 3) %}\n    {{i}}\n  {% endfor %}\n"), "  0\n  1\n  2\n")

    def test_simple_join(self):
        self.assertEqual(templaty.evaluate("{% join i in range(0, 3) with ',' %}{{i}}{% endjoin %}"), "0,1,2")

    def test_if_else(self):
        self.assertEqual(templaty.evaluate("{% if True %}Yes!{% endif %}"), "Yes!")
        self.assertEqual(templaty.evaluate("{% if False %}Yes!{% endif %}"), "")
        self.assertEqual(templaty.evaluate("{% if True %}Yes!{% else %}No!{% endif %}"), "Yes!")
        self.assertEqual(templaty.evaluate("{% if False %}Yes!{% else %}No!{% endif %}"), "No!")

    def test_elif(self):
        self.assertEqual(templaty.evaluate("{% if 1 == 2 %}Wrong.{% elif 1 == 1 %}Right{% endif %}"), "Right")
        self.assertEqual(templaty.evaluate("{% if 1 == 2 %}Wrong.{% elif 1 == 3 %}Still wrong.{% endif %}"), "")
        self.assertEqual(templaty.evaluate("{% if 1 == 2 %}Wrong.{% elif 1 == 3 %}Still wrong.{% else %}Right{% endif %}"), "Right")

    def test_member_access(self):
        self.assertEqual(templaty.evaluate("{{foo.bar.baz}}", {'foo':{'bar':{'baz':42}}}), '42')

