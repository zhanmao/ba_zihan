from typing import List

from examon_core.protocols import HintsProtocol


class HintsFactory(HintsProtocol):
    def build(self, _function: str, _answer: str, hints: List[str]) -> List[str]:
        return hints
