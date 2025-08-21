import logging
from typing import Callable, List, Type

from examon_core.code_execution.code_execution_sandbox import CodeExecutionSandbox
from examon_core.global_settings import ExamonGlobalSettings
from examon_core.models.question import Question
from examon_core.protocols import (
    CodeExecutionDriverProtocol,
    CodeMetricsProtocol,
    DifficultyProtocol,
    ExamonFactoryProtocol,
    HintsProtocol,
    MultiChoiceProtocol,
    UniqueIdProtocol,
)
from examon_core.protocols.function_to_string import FunctionToStringProtocol
from examon_core.protocols.tags import TagsProtocol

from .metrics import MetricsFactory


class ExamonFactory(ExamonFactoryProtocol):
    def __init__(
        self,
        code_execution_driver_class: Type[CodeExecutionDriverProtocol] = None,
        multi_choice_class: Type[MultiChoiceProtocol] = None,
        calc_standard_metrics_class: Type[CodeMetricsProtocol] = None,
        categorize_difficulty_class: Type[DifficultyProtocol] = None,
        unique_id_class: Type[UniqueIdProtocol] = None,
        function_to_string_class: Type[FunctionToStringProtocol] = None,
        hints_class: Type[HintsProtocol] = None,
        tags_class: Type[TagsProtocol] = None,
    ) -> None:
        self.code_execution_driver_class = code_execution_driver_class
        self.multi_choice_class = multi_choice_class
        self.calc_standard_metrics_class = calc_standard_metrics_class
        self.categorize_difficulty_class = categorize_difficulty_class
        self.unique_id_class = unique_id_class
        self.function_to_string_class = function_to_string_class
        self.hints_class = hints_class
        self.tags_class = tags_class

    def build(
        self,
        function: Callable = None,
        tags: List[str] = None,
        internal_id: str = None,
        hints: List[str] = None,
        choices: List[str] = None,
        repository: str = None,
        version: str = None,
        metrics: bool = None,
    ):
        function_src = self.function_to_string_class().build(function)
        print_logs = CodeExecutionSandbox(self.code_execution_driver_class).execute(
            function_src
        )
        answer = print_logs[-1]
        question = Question(
            function_src=function_src,
            print_logs=print_logs,
            correct_answer=answer,
        )
        question.hints = self.hints_class().build(function_src, answer, hints)
        question.unique_id = self.unique_id_class().run(question.function_src)
        question.tags = self.tags_class().build(function_src, answer, tags)

        if choices := self.normalize_choices(choices):
            question.choices = self.multi_choice_class(answer, choices).build()

        if metrics:
            question.metrics = MetricsFactory(
                calc_standard_metrics_class=self.calc_standard_metrics_class,
                categorize_difficulty_class=self.categorize_difficulty_class,
            ).build(question.function_src)

        question.internal_id = internal_id
        question.repository = repository
        question.version = version

        logging.debug(f"QuestionFactory.build: {question}")
        return question

    def normalize_choices(self, choices) -> List[str]:
        result_choice_list = []
        if choices:
            result_choice_list = list(map(lambda x: str(x), choices))
        return result_choice_list

    @staticmethod
    def default_instance(
        code_execution_driver_class: Type[CodeExecutionDriverProtocol] = None,
        multi_choice_factory_class: Type[MultiChoiceProtocol] = None,
        calc_standard_metrics_class: Type[CodeMetricsProtocol] = None,
        categorize_difficulty_class: Type[DifficultyProtocol] = None,
        unique_id_class: Type[UniqueIdProtocol] = None,
        code_to_string_class: Type[FunctionToStringProtocol] = None,
        hints_class: Type[HintsProtocol] = None,
        tags_class: Type[TagsProtocol] = None,
    ) -> ExamonFactoryProtocol:
        return ExamonFactory(
            code_execution_driver_class=code_execution_driver_class
            or ExamonGlobalSettings.code_execution_driver_class,
            multi_choice_class=multi_choice_factory_class
            or ExamonGlobalSettings.multi_choice_class,
            calc_standard_metrics_class=calc_standard_metrics_class
            or ExamonGlobalSettings.standard_metrics_calculator_class,
            categorize_difficulty_class=categorize_difficulty_class
            or ExamonGlobalSettings.difficulty_class_categorisor,
            unique_id_class=unique_id_class or ExamonGlobalSettings.unique_id_class,
            function_to_string_class=code_to_string_class
            or ExamonGlobalSettings.code_to_string_class,
            hints_class=hints_class or ExamonGlobalSettings.hints_class,
            tags_class=tags_class or ExamonGlobalSettings.tags_class,
        )
