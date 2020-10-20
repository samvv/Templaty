#!/usr/bin/env python3

from glob import glob
import argparse
import templaty
from difflib import Differ
import os
import sys

def write_diff(actual, expected):
    sys.stderr.writelines(Differ().compare(actual.splitlines(keepends=True), expected.splitlines(keepends=True)))

def do_save_cmd(args):
    for pattern in args.files:
        for path in glob(pattern):
            print(f"Saving {path} ...")
            with open(path, 'r') as f:
                contents = f.read()
            try:
                with open(path + '.output', 'r') as f:
                    expected = f.read()
            except FileNotFoundError:
                expected = ''
            new_expected = templaty.evaluate(contents, filename=path)
            if expected != new_expected:
                write_diff(expected, new_expected)
            with open(path + '.output', 'w') as f:
                f.write(new_expected)
    return 0

def do_run_cmd(args):
    exit_code = 0
    for pattern in args.files if 'files' in args else ['test-snippets/*.tply']:
        for path in glob(pattern):
            filename = os.path.basename(path)
            print(f"Checking {filename} ...")
            with open(path, 'r') as f:
                contents = f.read()
            actual = templaty.evaluate(contents, filename=path)
            try:
                with open(path + '.output', 'r') as f:
                    expected = f.read()
            except FileNotFoundError:
                print(f"Warning: {filename} does not have an expected output. Run 'test.py save {path}' to add it.")
                write_diff('', actual)
                continue
            if actual != expected:
                print("Error: output does not correspond with saved state")
                write_diff(actual, expected)
                exit_code = 1
    return exit_code

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()
save_parser = subparsers.add_parser('save')
save_parser.add_argument('files', nargs='*', default=['test-snippets/*.tply'])
save_parser.set_defaults(func=do_save_cmd)
run_parser = subparsers.add_parser('run')
run_parser.add_argument('files', nargs='*', default=['test-snippets/*.tply'])
run_parser.set_defaults(func=do_run_cmd)
args = parser.parse_args()

if 'func' in args:
    args.func(args)
else:
    do_run_cmd(args)

