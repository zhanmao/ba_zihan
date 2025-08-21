from typing import List, Protocol


class TagsProtocol(Protocol):

    def build(self, function: str, answer: str, tags: List[str]) -> List[str]: ...
