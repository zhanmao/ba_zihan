import ast
from collections import defaultdict
from types import MethodType

from examon_core.metrics.visit_methods import visit_methods


class CodeAnalysisVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.functions = set()
        self.calls = set()
        self.modules = set()
        self.counts = defaultdict(int)
        for visit_method in visit_methods:
            self.counts[visit_method] = 0
            env_setter = self.make_visit(visit_method)
            method = MethodType(env_setter, self)
            setattr(self, f"visit_{visit_method}", method)

    def record(self, node):
        self.counts[type(node).__name__] += 1

    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node) -> None:
        if node.func.__class__ == ast.Name:
            self.calls.add(node.func.id)
        elif node.func.__class__ == ast.Attribute:
            self.calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_Import(self, node) -> None:
        for name in node.names:
            self.modules.add(name.name.split(".")[0])

    def visit_ImportFrom(self, node) -> None:
        if node.module is not None and node.level == 0:
            self.modules.add(node.module.split(".")[0])

    @staticmethod
    def make_visit(_):
        def visit(self, node):
            self.record(node)
            self.generic_visit(node)

        return visit
