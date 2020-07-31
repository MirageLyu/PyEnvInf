import ast
import imp
import sys

sys.setrecursionlimit(10000)


class ParserVisitor(ast.NodeVisitor):

    def __init__(self):
        self.import_names = set()
        self.import_libraries = set()
        self.prefixes = {}
        self.aliases = {}
        self.calls = set()

    def is_standard_library(self, name):
        try:
            path = imp.find_module(name)[1]
            return bool(imp.is_builtin(name) or ('site-packages' not in path and 'Extras' not in path))
        except ImportError:
            return False

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname is not None:
                self.aliases[alias.asname] = alias.name
                self.import_names.add(alias.asname)
            else:
                self.import_names.add(alias.name)

            if alias.name and not self.is_standard_library(alias.name):
                self.import_libraries.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.asname is not None:
                self.aliases[alias.asname] = alias.name
                self.import_names.add(alias.asname)
            else:
                self.import_names.add(alias.name)

            if node.module and not self.is_standard_library(node.module):
                self.import_libraries.add(node.module)
                self.prefixes[alias.name] = node.module
        self.generic_visit(node)

    def visit_Assign(self, node):
        if type(node.value) is ast.Name and node.value.id in self.import_names:
            for target in node.targets:
                if hasattr(node.value, 'id'):
                    if type(target) is ast.Attribute and hasattr(target.value, 'id'):
                        self.aliases[target.value.id] = node.value.id
                    elif hasattr(target, 'id'):
                        self.aliases[target.id] = node.value.id
        self.generic_visit(node)

    def visit_Call(self, node):
        self.calls.add(self.call_to_string(node))
        self.generic_visit(node)

    def call_to_string(self, node):
        prefix, suffix = self.get_call_function_segments(node.func)

        if prefix in self.aliases:
            prefix = self.aliases[prefix]

        if prefix in self.prefixes:
            prefix = '{}.{}'.format(self.prefixes[prefix], prefix)

        return '{}{}'.format(prefix, suffix)

    def get_call_function_segments(self, call):
        t = type(call)

        if t is ast.Name:
            return (call.id, '')
        elif t is ast.Attribute:
            prefix, suffix = self.get_call_function_segments(call.value)
            return (
                prefix,
                '{}.{}'.format(suffix, call.attr)
                if suffix is not None
                else call.attr
            )
        elif t is ast.Call:
            return self.get_call_function_segments(call.func)
        else:
            return (t.__name__.lower(), '')
