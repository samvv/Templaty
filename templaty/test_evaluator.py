
import templaty
from types import SimpleNamespace

def test_if_else():
    assert(templaty.evaluate("{% if True %}Yes!{% endif %}") == "Yes!")
    assert(templaty.evaluate("{% if False %}Yes!{% endif %}") == "")
    assert(templaty.evaluate("{% if True %}Yes!{% else %}No!{% endif %}") == "Yes!")
    assert(templaty.evaluate("{% if False %}Yes!{% else %}No!{% endif %}") == "No!")

def test_elif():
    assert(templaty.evaluate("{% if 1 == 2 %}Wrong.{% elif 1 == 1 %}Right{% endif %}") == "Right")
    assert(templaty.evaluate("{% if 1 == 2 %}Wrong.{% elif 1 == 3 %}Still wrong.{% endif %}") == "")
    assert(templaty.evaluate("{% if 1 == 2 %}Wrong.{% elif 1 == 3 %}Still wrong.{% else %}Right{% endif %}") == "Right")

def test_member_access():
    assert(templaty.evaluate("{{foo.bar.baz}}", {'foo': SimpleNamespace(bar=SimpleNamespace(baz=42)) }) == '42')

def test_chain_operator():
    assert(templaty.evaluate("{{'foo-bar' |> snake |> upper}}") == 'FOO_BAR')

def test_index_expression():
    assert(templaty.evaluate("{{foo[1]}}", { 'foo': [1, 2, 3] }) == '2')

def test_slice_expression():
    assert(templaty.evaluate("{{foo[1:3][0]}}", { 'foo': [1, 2, 3] }) == '2')
    assert(templaty.evaluate("{{foo[1:3][1]}}", { 'foo': [1, 2, 3] }) == '3')

def test_variable_existence():
    assert(templaty.evaluate("{{'foo' in globals()}}", { 'foo': 42 }) == 'True')
    assert(templaty.evaluate("{{'foo' in globals()}}") == 'False')

