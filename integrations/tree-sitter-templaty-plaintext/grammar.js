module.exports = grammar({

  name: 'templaty',

  extras: $ => [],

  word: $ => $.identifier,

  rules: {

    source_file: $ => repeat($._statement),

    _newline: $ => /\n/,

    // Pseudo Python grammar

    string: $ => choice(
      seq('"', /[^"]*/, '"'),
      seq('\'', /[^']*/, '\''),
    ),

    integer: $ => /[0-9]+/,

    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,

    reference_expression: $ => $.identifier,

    literal_expression: $ => choice(
      $.string,
      $.integer,
    ),

    _pattern: $ => choice(
      $.var_pattern,
      $.tuple_pattern,
    ),

    // Templaty grammar

    _statement: $ => choice(
      $.for_in_statement,
      $.expression_statement,
      $.join_statement,
      $.text_statement,
    ),

    _expression: $ => choice(
      $.reference_expression,
      $.literal_expression,
    ),

    _ws: $ => /\s*/,

    var_pattern: $ => $.identifier,

    tuple_pattern: $ => seq('(', $._ws, optional(seq($._pattern, $._ws, repeat(seq(',', $._ws, $._pattern)))), ')'),

    expression_statement: $ => seq('{{', $._expression, '}}'),

    join_statement: $ => seq(
      '{%',
      $._ws,
      'join',
      $._ws,
      $._pattern,
      $._ws,
      'in',
      $._ws,
      $._expression,
      $._ws,
      'with',
      $._expression,
      $._ws,
      '%}',
      repeat($._statement),
      '{%',
      $._ws,
      'endjoin',
      $._ws,
      '%}'
    ),

    for_in_statement: $ => seq(
      '{%',
      $._ws,
      'for',
      $._ws,
      $._pattern,
      $._ws,
      'in',
      $._ws,
      $._expression,
      $._ws,
      '%}',
      repeat($._statement),
      '{%',
      $._ws,
      'endfor',
      $._ws,
      '%}'
    ),

    text_statement: $ => /[^{]+|\{/

  }

});
