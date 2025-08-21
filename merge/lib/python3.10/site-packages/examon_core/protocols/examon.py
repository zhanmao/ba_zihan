from typing import Any, Callable, List, Protocol

from examon_core.models.question import Question


class ExamonFactoryProtocol(Protocol):
    def build(
        self,
        function: Callable = None,
        tags: List[str] = None,
        internal_id: str = None,
        hints: List[str] = None,
        choices: List[Any] = None,
        repository: str = None,
        version: str = None,
        metrics: bool = None,
    ) -> Question:
        pass
