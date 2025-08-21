from typing import Protocol


class UniqueIdProtocol(Protocol):
    def run(self, function_src: str) -> str: ...
