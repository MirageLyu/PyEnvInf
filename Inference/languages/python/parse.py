from __future__ import with_statement
import ast
import getopt
import json
import os
import sys
from visitor import ParserVisitor

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def parse_method_call_tokens(snippet):
    try:
        # Parse snippet into an abstract syntax tree
        tree = ast.parse(str(snippet))

        # Parse the ast
        visitor = ParserVisitor()
        visitor.visit(tree)

        # Get imports and calls
        imports = list(visitor.import_libraries)
        calls = list(visitor.calls)
    except SyntaxError:
        imports = []
        calls = []

    # Return
    return {'imports': imports, 'calls': calls}


def parse_file(filename):
    # Tokenize
    with open(os.path.abspath(filename), 'r') as input_file:
        return parse_method_call_tokens(input_file.read())


def main():
    # Get command line arguments
    opts, args = getopt.getopt(sys.argv[1:], '', [])

    # Generate absolute path name
    if not args:
        raise Exception('Usage: python parse.py <filename>')
    pathname = os.path.abspath(args[0])

    # Import data
    data = {}

    # If pathname is a directory, iterate over all top level python files
    if os.path.isdir(pathname):
        for filename in os.listdir(pathname):
            filename = os.path.join(pathname, filename)
            fname, fext = os.path.splitext(filename)
            if os.path.isfile(filename) and fext == '.py':
                data[filename] = parse_file(filename)
    # If pathname is a file, attempt to parse it
    elif os.path.isfile(pathname):
        data[pathname] = parse_file(pathname)
    else:
        print("{} is not a directory or file.".format(pathname))

    # Print to stdout
    print(json.dumps(data))
