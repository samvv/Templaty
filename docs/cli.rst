Command-Line Interface
======================

Templaty comes with a simple command-line interface (CLI) so that you don't
have to write a single line of Python code. The command is called ``templaty``
and is available by default when installing using ``pip install``.

Examples
--------

Writing the resulting text of a Templaty file to *stdout*:

.. code-block:: none

  templaty mytemplate.tply

Passing data to the template in JSON format:

.. code-block:: none

  echo '{"author":"Sam Vervaeck","copyright":"2019"}' | templaty mytemplate.cc.tply --stdin
