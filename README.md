Templaty
========

[![Documentation Status](https://readthedocs.org/projects/templaty/badge/?version=latest)](https://templaty.readthedocs.io/en/latest/?badge=latest)

**Templaty** is a code generator written in Python that focuses on generating
code for programming languages other than HTML. It features fine-grained
control over whitespacing and indentation and a rich meta-language that allows 
full control over the code to be generated.

The template syntax was inspired by [Jinja2][1] and should be very easy to pick
up.

```
def sum_all_answers():
  {% for i in range(0, 10) %}
    answer{{i+1}} = {% if i % 2 == 0 %}get_input_from_alice(){% else %}get_input_from_bob(){% endif %}
  {% endfor %}
  return {% join i in range(0, 10) with ' + ' %}answer{{i+1}}{% endjoin %}
```

Generates the following code:

```
def sum_all_answers():
  answer1 = get_input_from_alice()
  answer2 = get_input_from_bob() 
  answer3 = get_input_from_alice() 
  answer4 = get_input_from_bob() 
  answer5 = get_input_from_alice() 
  answer6 = get_input_from_bob() 
  answer7 = get_input_from_alice() 
  answer8 = get_input_from_bob() 
  answer9 = get_input_from_alice() 
  answer10 = get_input_from_bob() 
  return answer1 + answer2 + answer3 + answer4 + answer5 + answer6 + answer7 + answer8 + answer9 + answer10
```

[1]: https://jinja.palletsprojects.com/

## Usage

Eventually, Templaty will be available on PyPi and you'll be able to issue the following command:

```
pip3 install -U --user templaty
```

This should make the main command `templaty` available in your terminal.

## FAQ

### Will this library support Python 2?

No. Python 2 has reached its end-of-life and the organisation recommends
everyone to upgrade to Python 3. Porting to Python 2 requires extra work
for no good reason.

### Is it safe to use this library in my web server?

No, absolutely not! Templaty is a tool meant to be run by developers, not
end-users. As such, it has little (if any) security checks. You should never
run untrusted input using Templaty, only code you wrote yourself or from a
developer you trust.

## License

Templaty is licensed under the MIT license, in the hope it will help developers
write better programs.

