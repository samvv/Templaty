Templaty
========

[![Documentation Status](https://readthedocs.org/projects/templaty/badge/?version=latest)](https://templaty.readthedocs.io/en/latest/?badge=latest)

**Templaty** is a code generator written in Python that focuses on generating
correct and readable programming code. It features fine-grained control over
whitespacing and indentation and a rich meta-language that allows full control
over the end result.

🌈 There now is [a syntax plugin for Vim][2]!

The template syntax was inspired by [Jinja2][1] and should be very easy to pick
up.

```
def annoying_prompt():
    {% for i in range(0, 5) %}
      prompt("Hey, how you're doing?")
    {% endfor %}
```

Generates the following code:

```python
def annoying_prompt():
    prompt("Hey, how you're doing?")
    prompt("Hey, how you're doing?")
    prompt("Hey, how you're doing?")
    prompt("Hey, how you're doing?")
    prompt("Hey, how you're doing?")
```

What about generating an [identity matrix][3] in C that imposes no runtime cost?

```
static const int IDENTITY_MATRIX[][] = [
  {% join i in range(0, 10) with ',' %}
    [{% join j in range(0, 10) with ',' %}{% if j == i %}1{% else %}0{% endif %}{% endjoin %}]
  {% endjoin %}
];
```

It should look something like this:

```c
static const int IDENTITY_MATRIX[][] = [
  [1,0,0,0,0,0,0,0,0,0],
  [0,1,0,0,0,0,0,0,0,0],
  [0,0,1,0,0,0,0,0,0,0],
  [0,0,0,1,0,0,0,0,0,0],
  [0,0,0,0,1,0,0,0,0,0],
  [0,0,0,0,0,1,0,0,0,0],
  [0,0,0,0,0,0,1,0,0,0],
  [0,0,0,0,0,0,0,1,0,0],
  [0,0,0,0,0,0,0,0,1,0],
  [0,0,0,0,0,0,0,0,0,1]
];
```

This is just the tip of the iceberg of what Templaty can do!

## Usage

Templaty is available on PyPi. You can issue the following command to install it:

```sh
pip3 install -U --user templaty
```

This should make the main command `templaty` available in your terminal.

This should make the main command `templaty` available in your terminal.

## IDE Integration

### Neovim

⚠️ These instructions are stil under development.

First you must clone this repository. It contains definitions for
_tree-sitter_, which Neovim can use.

```sh
git clone https://github.com/samvv/Templaty
```

Next, configure these parsers in `init.lua`:

```lua
local parser_config = require "nvim-treesitter.parsers".get_parser_configs()

parser_config.templaty = {
  install_info = {
    url = "/path/to/cloned/repo/integrations/tree-sitter-templaty-plaintext",
    files = {"src/parser.c"},
    -- branch = "main",
    generate_requires_npm = false,
    requires_generate_from_grammar = false,
  },
  filetype = "templaty", 
}

parser_config.templatypython = {
  install_info = {
    url = "/path/to/cloned/repo/integrations/tree-sitter-templaty-python",
    files = {"src/parser.c", "src/scanner.c"},
    -- branch = "main",
    generate_requires_npm = false,
    requires_generate_from_grammar = false,
  },
  filetype = "templaty.python",
}
```

You will also need to configure Neovim to detect these files as `templaty.python` etc.

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

### What extension should I use for my template files?

It is recommended to use the `.tply` extension so that syntax plugins like 
[vim-templaty][2] automatically set up the right syntax highlighting for you.

If your template contains code in another programming language, simply prefix
the default file extension to `.tply`, e.g. `mytemplate.cc.tply`.

## License

Templaty is licensed under the Apache 2.0 license, in the hope it will help developers
write better programs.

[1]: https://jinja.palletsprojects.com/
[2]: https://github.com/samvv/vim-templaty
[3]: https://en.wikipedia.org/wiki/Identity_matrix
