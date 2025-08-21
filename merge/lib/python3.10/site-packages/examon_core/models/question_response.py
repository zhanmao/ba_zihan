from dataclasses import dataclass

from examon_core.models.question import Question


@dataclass
class QuestionResponse:
    question: Question = None
    response: str = None
    correct: bool = None
