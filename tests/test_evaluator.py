
import templaty
import unittest
from types import SimpleNamespace

class TestEvaluator(unittest.TestCase):

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
        self.assertEqual(templaty.evaluate("{{foo.bar.baz}}", {'foo': SimpleNamespace(bar=SimpleNamespace(baz=42)) }), '42')

    def test_chain_operator(self):
        self.assertEqual(templaty.evaluate("{{'foo-bar' |> snake |> upper}}"), 'FOO_BAR')

    def test_index_expression(self):
        self.assertEqual(templaty.evaluate("{{foo[1]}}", { 'foo': [1, 2, 3] }), '2')

    def test_slice_expression(self):
        self.assertEqual(templaty.evaluate("{{foo[1:3][0]}}", { 'foo': [1, 2, 3] }), '2')
        self.assertEqual(templaty.evaluate("{{foo[1:3][1]}}", { 'foo': [1, 2, 3] }), '3')


