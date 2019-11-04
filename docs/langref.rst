Templaty Language Reference
===========================

This page explains in detail how the Templaty language is structured.

Regular Text
------------

Regular text is just passed along as-is, without any preprocessing done to it.

Expressions
-----------

Expressions are used in the control-flow statements and can also appear
anywhere in the template to generate specific text.

Variable References
^^^^^^^^^^^^^^^^^^^

Any identifier that is not a keyword may be used to reference one of the
built-in expressions or an expression that was defined elsewhere in the
template.

.. code-block:: none

  This file was generated on {{now}} by {{author}}.

Control Flow
------------

The following statements are used in Templaty to change what text is written
when the template is run. Most of them should be very familiar, as they
resemble the constructs found in most regular programming languages.

Conditional Code Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Conditionals are used to generate a piece of text depending on whether a given
predicate is met. Just like in regular programming languages, you can have
conditionals with multiple alternatives or none at all.

.. code-block:: none

  {% if header %}
    // This header is only generated if header is set to true
    // in the environment. You can create a JSON file that contains
    // this variable, or define it somewhere in the template itself.
  {% endif %}

The ``else``-directive is used to provide some text when no predicate matched,
like so:

.. code-block:: none

  {% if long_header %}
    // This file does stuff. It is really cool because it first does 
    // stuff and then some more stuff. Once the stuff is finished, it calls
    // a thing to do other stuff.
  {% else %}
    // This file does stuff.
  {% endif %}

Generating Repititions
^^^^^^^^^^^^^^^^^^^^^^

Templates for code generation wouldn't be particularly useful if we couldn't
use them to auto-generate repetitive code. The ``for``-statement is one of the
simplest methods for generating (possibly huge) amounts of code.

.. code-block:: none

  {% for i in range(1, 10) %}
    prompt("Attempt no {{i}}");
  {% endfor %}
  error("I gave up.");

The above snippet will generate the following code:

.. code-block:: none

  prompt("Attempt no 1");
  prompt("Attempt no 2");
  prompt("Attempt no 3");
  prompt("Attempt no 4");
  prompt("Attempt no 5");
  prompt("Attempt no 6");
  prompt("Attempt no 7");
  prompt("Attempt no 8");
  prompt("Attempt no 9");
  error("I gave up.");

Built-in Variables
------------------

Templaty contains a growing number of built-in variables to make it easy for
programmers to write their templates without much hassle. The folllowing is an
incomplete list of functions and variables that are supported out-of-the-box.

``now``
  A variable holding the time the generator started, formatted using some default rules.

``a + b``
  Add two expressions to each other.

``a - b``
  Subtract two expressions from one another.

``a % b``
  Find the remainder after the division of the two given numbers.

