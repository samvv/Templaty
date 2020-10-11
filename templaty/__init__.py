
import os

from .main import main
from .evaluator import evaluate

def execute(filepath, ctx={}, **kwargs):
    with open(filepath, 'r') as f:
        contents = f.read()
    return evaluate(contents, ctx, filename=os.path.relpath(str(filepath), os.getcwd()), **kwargs)

