
from datetime import datetime

from templaty.evaluator import func, getter, VariableBuiltin, FunctionBuiltin

@func('range')
def my_range(a, b):
    return range(a, b)

@func('+')
def my_plus(a, b):
    return a + b

@func('-')
def my_minus(a ,b):
    return a - b

class NowBuiltin(VariableBuiltin):

    name = 'now'

    def __init__(self):
        self.timestamp = datetime.now()

    def get(self):
        return self.timestamp.strftime("%b %d %Y %H:%M:%S")

