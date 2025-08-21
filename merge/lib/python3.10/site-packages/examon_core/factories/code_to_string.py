from examon_core.models.python_code_convertor import (
    AppendPrint,
    PythonCodeConvertor,
    RemovePythonDecorators,
)
from examon_core.protocols.function_to_string import FunctionToStringProtocol


class CodeToStringFactory(FunctionToStringProtocol):
    def build(self, function) -> str:
        return PythonCodeConvertor(
            [RemovePythonDecorators(), AppendPrint(function.__name__)]
        ).build(function)
