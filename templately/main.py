
import os, sys
import argparse

from .scanner import Scanner
from .parser import Parser
from .evaluator import evaluate

def main(argv=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The template file from which code will be generated.')
    args = parser.parse_args(argv)

    with open(args.file, 'r') as f:
        contents = f.read()

    sc = Scanner(args.file, contents)
    p = Parser(sc)
    ss = p.parse_all()

    evaluate(ss, sys.stdout)

