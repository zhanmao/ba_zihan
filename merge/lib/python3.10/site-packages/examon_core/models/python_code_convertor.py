import inspect
import logging
from typing import List

from examon_core.protocols import CodeDecoratorProtocol
from examon_core.protocols.function_to_string import FunctionToStringProtocol


class PythonCodeConvertor(FunctionToStringProtocol):
    def __init__(self, decorators: List = None) -> None:
        self.decorators = [] if decorators is None else decorators

    def build(self, function) -> str:
        src_code = self.function_src(function)
        for decorator in self.decorators:
            logging.debug(f"PythonCodeConvertor.build: {decorator}")
            src_code = decorator.decorate(src_code)
            logging.debug(f"PythonCodeConvertor.build: {src_code}")

        logging.debug(f"PythonCodeConvertor.build: {src_code}")
        return src_code

    def function_src(self, function):
        logging.debug(f"PythonCodeConvertor.function_src: {function}")
        return inspect.getsource(function).strip()


class SourceCodeComments(CodeDecoratorProtocol):
    def __init__(self, hints: List[str]) -> None:
        self.hints = hints or []

    def decorate(self, src_code) -> str:
        all_hints = "\n".join(f"# {hint}" for hint in self.hints)
        return f"# Hints:\n{all_hints}\n\n{src_code}" if all_hints else src_code


class RemovePythonDecorators(CodeDecoratorProtocol):
    def decorate(self, src_code) -> str:
        return src_code[src_code.find("def") :]


class AppendPrint(CodeDecoratorProtocol):
    def __init__(self, function_name) -> None:
        self.function_name = function_name

    def decorate(self, src_code) -> str:
        println = f"\n\nprint({self.function_name}())"
        return src_code + println
