
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
    for t1 in sc.scan_all():
        print(t1.get_text(contents))

