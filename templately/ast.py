
class Node:

    def __init__(self, parent=None):
        self.parent = parent

class Pattern(Node):
    pass

class VarPattern(Pattern):

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name

class Expression(Node):
    pass

class VarRefExpression(Expression):

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name


class ConstExpression(Expression):

    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.value = value

class AppExpression(Expression):

    def __init__(self, operator, operands, parent=None):
        super().__init__(parent)
        self.operator = operator
        self.operands = operands

class Statement(Node):
    pass

class TextStatement(Statement):

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text

class ForInStatement(Statement):

    def __init__(self, pattern, expression, body, parent=None):
        super().__init__(parent)
        self.pattern = pattern
        self.expression = expression
        self.body = body

