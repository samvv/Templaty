
import sys
import argparse
import json

from .scanner import Scanner
from .parser import Parser
from .evaluator import evaluate

def main(argv=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The template file from which code will be generated.')
    input_flags = parser.add_mutually_exclusive_group()
    input_flags.add_argument('--data-file', help='A JSON file containing variables that will be passed to the template')
    input_flags.add_argument('--stdin', action='store_true', help='When present, reads JSON data from STDIN and passes it to the template')

    args = parser.parse_args(argv)

    if args.data_file is not None:
        with open(args.data_file, 'r') as f:
            data = json.loads(f.read())
    elif args.stdin:
        data = json.loads(sys.stdin.read())
    else:
        data = {}

    with open(args.file, 'r') as f:
        contents = f.read()

    # sc = Scanner(args.file, contents)
    # p = Parser(sc)
    # root_node = p.parse_all()
    # set_parent_nodes(root_node)

    print(evaluate(contents, data, filename=args.file))


