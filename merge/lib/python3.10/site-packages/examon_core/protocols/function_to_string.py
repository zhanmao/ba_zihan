from typing import Protocol


class FunctionToStringProtocol(Protocol):

    def build(self, function) -> str: ...
