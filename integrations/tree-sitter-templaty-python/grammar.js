
const Py = require('tree-sitter-python/grammar')

const MAX_PREC = Py.PREC.call;

module.exports = grammar(Py, {

  name: 'templatypython',

  // extras: $ => [],

  // word: $ => $.identifier,

  conflicts: $ => [

    // Templaty
    [$.expression, $._templaty_statement],

    // Python
    [$.primary_expression, $.pattern],
    [$.primary_expression, $.list_splat_pattern],
    [$.tuple, $.tuple_pattern],
    [$.list, $.list_pattern],
    [$.with_item, $._collection_elements],
    [$.named_expression, $.as_pattern],
    [$.print_statement, $.primary_expression],
    [$.type_alias_statement, $.primary_expression],

  ],

  rules: {

    source_file: $ => repeat($._statement),

    expression: ($, original) => choice(
      original,
      $.templaty_expression_statement
    ),

    _statement: ($, original) => choice(
      prec(MAX_PREC + 1, original),
      $._templaty_statement,
    ),

    _newline: $ => /\n/,

    _templaty_statement: $ => choice(
      $.templaty_for_in_statement,
      $.templaty_expression_statement,
      $.templaty_join_statement,
      //$.templaty_text_statement,
    ),

    _ws: $ => /\s*/,

    templaty_expression_statement: $ => seq('{{', $.expression, '}}'),

    templaty_join_statement: $ => seq(
      '{%',
      $._ws,
      'join',
      $._ws,
      $.pattern,
      $._ws,
      'in',
      $._ws,
      $.expression,
      $._ws,
      'with',
      $.expression,
      $._ws,
      '%}',
      repeat($._statement),
      '{%',
      $._ws,
      'endjoin',
      $._ws,
      '%}'
    ),

    templaty_for_in_statement: $ => seq(
      '{%',
      $._ws,
      'for',
      $._ws,
      $.pattern,
      $._ws,
      'in',
      $._ws,
      $.expression,
      $._ws,
      '%}',
      repeat($._statement),
      '{%',
      $._ws,
      'endfor',
      $._ws,
      '%}'
    ),

    //templaty_text_statement: $ => /[^{]+|\{/
  }
});
