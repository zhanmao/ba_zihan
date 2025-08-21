import logging
import random
from typing import List

from examon_core.filter_options import FilterOptions
from examon_core.models.question import Question


class InMemoryDB:
    __registry = []
    __tags = []

    @classmethod
    def add(cls, examon_item) -> None:
        logging.debug(f"Adding {examon_item} to registry")
        cls.__registry.append(examon_item)
        cls.__tags.extend(tag for tag in examon_item.tags if tag not in cls.__tags)

    @classmethod
    def purge(cls) -> None:
        cls.__registry = []
        cls.__tags = []

    @classmethod
    def shuffle(cls) -> None:
        random.shuffle(cls.__registry)

    @classmethod
    def load(cls, filter_options: FilterOptions = None) -> List[Question]:
        results = cls.__registry
        if filter_options is None:
            return results

        def intersection(lst1: list[str], lst2: list[str]) -> list[str]:
            return list(set(lst1) & set(lst2))

        def array_contains_any(array: list[str], has_one: list[str]) -> bool:
            return len(intersection(array, has_one)) > 0

        def array_contains_all(array: list[str], has_all: list[str]) -> bool:
            return len(intersection(array, has_all)) == len(has_all)

        if filter_options.tags_any is not None:
            results = [
                questions
                for questions in cls.__registry
                if array_contains_any(filter_options.tags_any, questions.tags)
            ]
        if filter_options.tags_all is not None:
            results = [
                questions
                for questions in cls.__registry
                if array_contains_all(filter_options.tags_all, questions.tags)
            ]
        if filter_options.difficulty_category is not None:
            results = [
                questions
                for questions in cls.__registry
                if filter_options.difficulty_category
                == questions.metrics.categorised_difficulty
            ]

        if filter_options.max_questions is not None:
            results = results[: filter_options.max_questions]
        return results

    @classmethod
    def unique_tags(cls) -> List[str]:
        return cls.__tags
