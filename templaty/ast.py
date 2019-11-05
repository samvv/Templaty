
class Node:
    pass

class Pattern(Node):
    pass

class VarPattern(Pattern):

    def __init__(self, name):
        super().__init__()
        self.name = name

class Expression(Node):
    pass

class VarRefExpression(Expression):

    def __init__(self, name):
        super().__init__()
        self.name = name


class ConstExpression(Expression):

    def __init__(self, value):
        super().__init__()
        self.value = value

class AppExpression(Expression):

    def __init__(self, operator, operands):
        super().__init__()
        self.operator = operator
        self.operands = operands

class Statement(Node):
    pass

class TextStatement(Statement):

    def __init__(self, text):
        super().__init__()
        self.text = text

class ExpressionStatement(Statement):

    def __init__(self, expression):
        super().__init__()
        self.expression = expression

class IfStatement(Statement):

    def __init__(self, cases, alternative):
        super().__init__()
        self.cases = cases
        self.alternative = alternative

class JoinStatement(Statement):

    def __init__(self, pattern, expression, separator, body):
        super().__init__()
        self.pattern = pattern
        self.expression = expression
        self.separator = separator
        self.body = body

    def to_json(self):
        return {
            'pattern': self.pattern.to_json(),
            'expression': self.expression.to_json(),
            'body': list(stmt.to_json() for stmt in self.body),
            'separator': self.separator.to_json()
            }

class ForInStatement(Statement):

    def __init__(self, pattern, expression, body):
        super().__init__()
        self.pattern = pattern
        self.expression = expression
        self.body = body

