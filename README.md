Templately
==========

**Templately** is a code generator written in Python that focuses on generating
code for programming languages other than HTML. It features fine-grained
control over whitespacing and indentation and supports custom Python routines
in the template itself.

## FAQ

### Is it safe to use this library in my web server?

No, absolutely not! Templately is a tool meant to be run by developers, not
end-users. As such, it has little (if any) security checks. You should never
run untrusted input using Templately, only code you wrote yourself or from a
developer you trust.

## Usage

Eventually, Templately will be available on PyPi and you'll be able to issue the following command:

```
pip3 install -U --user templately
```

This should make the main command `templately` available in your terminal.

## License

Templately is licensed under the MIT license, in the hope it will help developers
write better programs.

