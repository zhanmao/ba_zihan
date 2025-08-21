from dataclasses import dataclass

from examon_core.models.code_metrics import CodeMetrics


@dataclass
class Question:
    function_src: str = None
    unique_id: str = None
    internal_id: str = None
    tags: list = None
    repository: str = None
    hints: list = None
    print_logs: list = None
    correct_answer: str = None
    metrics: CodeMetrics = None
    choices: dict = None
    theme: str = None
    explanation: str = None

    def answer(self, given_answer: str):
        return str(self.correct_answer) == str(given_answer)
