
import argparse

from .scanner import Scanner
from .parser import Parser

def main(argv=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The template file from which code will be generated.')
    args = parser.parse_args(argv)

    with open(args.file, 'r') as f:
        contents = f.read()

    sc = Scanner(args.file, contents)
    p = Parser(sc)
    for e1 in p.parse_all():
        print(e1)

