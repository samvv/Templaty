Templately
==========

**Templately** is a code generator written in Python that focuses on generating
code for programming languages other than HTML. It features fine-grained
control over whitespacing and indentation and a rich meta-language that allows 
full control over the code to be generated.

The template syntax was inspired by [Jinja2][1] and should be very easy to pick
up.

```
{% for i in range(0, 10)}
  var foo{{i}} = 0;
{% endfor %}
```

[1]: https://jinja.palletsprojects.com/

## Usage

Eventually, Templately will be available on PyPi and you'll be able to issue the following command:

```
pip3 install -U --user templately
```

This should make the main command `templately` available in your terminal.

## FAQ

### Will this library support Python 2?

No. Python 2 has reached its end-of-life and the organisation recommends
everyone to upgrade to Python 3. Porting to Python 2 requires extra work
for no good reason.

### Is it safe to use this library in my web server?

No, absolutely not! Templately is a tool meant to be run by developers, not
end-users. As such, it has little (if any) security checks. You should never
run untrusted input using Templately, only code you wrote yourself or from a
developer you trust.

## License

Templately is licensed under the MIT license, in the hope it will help developers
write better programs.

