from typing import List, Protocol


class HintsProtocol(Protocol):

    def build(self, function: str, answer: str, hints: List[str]) -> List[str]: ...
