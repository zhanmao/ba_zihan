from typing import Protocol


class CodeDecoratorProtocol(Protocol):
    def decorate(self, code: str) -> str: ...
