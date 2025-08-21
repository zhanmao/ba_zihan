from dataclasses import dataclass
from typing import List


@dataclass
class FilterOptions:
    difficulty_category: str = None
    max_questions: int = None
    tags_any: List[str] = None
    tags_all: List[str] = None
