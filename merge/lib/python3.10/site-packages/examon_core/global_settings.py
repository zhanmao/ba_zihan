from examon_core.code_execution.unrestricted_driver import UnrestrictedDriver
from examon_core.factories.code_to_string import CodeToStringFactory
from examon_core.factories.hints import HintsFactory
from examon_core.factories.multi_choice import MultiChoiceFactory
from examon_core.factories.tags import TagsFactory
from examon_core.in_memory_db import InMemoryDB
from examon_core.metrics.difficulty_categorisor import DifficultyCategorisor
from examon_core.metrics.standard_metrics_calculator import StandardMetricsCalculator
from examon_core.unique_id_generator import UniqueIdGenerator


class ExamonGlobalSettings:
    record_metrics = True
    repository = None
    version = None

    code_to_string_class = CodeToStringFactory
    code_execution_driver_class = UnrestrictedDriver

    tags_class = TagsFactory
    hints_class = HintsFactory
    multi_choice_class = MultiChoiceFactory

    unique_id_class = UniqueIdGenerator
    standard_metrics_calculator_class = StandardMetricsCalculator
    difficulty_class_categorisor = DifficultyCategorisor

    database = InMemoryDB
