Templaty
========

**Templaty** is a code generator written in Python that focuses on generating
code for programming languages other than HTML. It features fine-grained
control over whitespacing and indentation and a rich meta-language that allows 
full control over the code to be generated.

The template syntax was inspired by [Jinja2][1] and should be very easy to pick
up.

```
def sum_all_foos():
  {% for i in range(0, 10) %}
    foo{{i+1}} = 1
  {% endfor %}
  return {% join i in range(0, 10) with ' + ' %}foo{{i+1}}{% endjoin %}
```

Generates the following code:

```
def sum_all_foos():
  foo1 = 1
  foo2 = 1
  foo3 = 1
  foo4 = 1
  foo5 = 1
  foo6 = 1
  foo7 = 1
  foo8 = 1
  foo9 = 1
  foo10 = 1
  return foo1 + foo2 + foo3 + foo4 + foo5 + foo6 + foo7 + foo8 + foo9 + foo10
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

