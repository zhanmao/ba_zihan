from typing import Callable, Protocol

from examon_core.models.question import Question


class QuestionFactoryProtocol(Protocol):
    def build(self, function: Callable) -> Question: ...
