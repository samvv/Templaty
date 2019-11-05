
from .main import main
from .evaluator import evaluate

def execute(filepath, ctx={}, **kwargs):
    with open(filepath, 'r') as f:
        contents = f.read()
    return evaluate(contents, ctx, filename=os.path.basename(filepath), **kwargs)

