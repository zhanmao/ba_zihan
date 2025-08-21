from typing import Protocol

from examon_core.models.code_metrics import CodeMetrics


class DifficultyProtocol(Protocol):
    def __init__(self, code_metrics: CodeMetrics) -> None: ...
    def run(self) -> str: ...
