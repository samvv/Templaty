
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


class Statement(Node):
    pass

class ForInStatement(Statement):

    def __init__(self, pattern, expression, body, parent=None):
        super().__init__(parent)
        self.pattern = pattern
        self.expression = expression
        self.body = body

