from typing import Any, List

from examon_core.factories.examon import ExamonFactory
from examon_core.global_settings import ExamonGlobalSettings
from examon_core.protocols import (
    CodeExecutionDriverProtocol,
    CodeMetricsProtocol,
    DifficultyProtocol,
    FunctionToStringProtocol,
    HintsProtocol,
    MultiChoiceProtocol,
    UniqueIdProtocol,
)


def examon(
    internal_id: str = None,
    choices: List[Any] = None,
    tags: List[str] = None,
    hints: List[str] = None,
    repository: str = None,
    record_metrics: bool = None,
    version: str = None,
    code_execution_driver_class: CodeExecutionDriverProtocol = None,
    standard_metrics_calculator_class: CodeMetricsProtocol = None,
    difficulty_categorise_class: DifficultyProtocol = None,
    function_to_string_class: FunctionToStringProtocol = None,
    unique_id_class: UniqueIdProtocol = None,
    multi_choice_class: MultiChoiceProtocol = None,
    hints_class: HintsProtocol = None,
):
    def inner_function(function):
        ExamonGlobalSettings.database.add(
            ExamonFactory.default_instance(
                code_execution_driver_class=code_execution_driver_class,
                calc_standard_metrics_class=standard_metrics_calculator_class,
                categorize_difficulty_class=difficulty_categorise_class,
                unique_id_class=unique_id_class,
                code_to_string_class=function_to_string_class,
                multi_choice_factory_class=multi_choice_class,
                hints_class=hints_class,
            ).build(
                function=function,
                internal_id=internal_id,
                choices=choices,
                tags=tags,
                hints=hints,
                repository=(repository or ExamonGlobalSettings.repository),
                version=version or ExamonGlobalSettings.version,
                metrics=(record_metrics or ExamonGlobalSettings.record_metrics),
            )
        )
        return function

    return inner_function
