import ast
import logging
from typing import Type

from examon_core.metrics.code_analysis_visitor import CodeAnalysisVisitor
from examon_core.models.code_metrics import CodeMetrics
from examon_core.protocols import CodeMetricsProtocol, DifficultyProtocol


class MetricsFactory(object):
    def __init__(
        self,
        calc_standard_metrics_class: Type[CodeMetricsProtocol],
        categorize_difficulty_class: Type[DifficultyProtocol],
    ) -> None:
        self.calc_standard_metrics_strategy = calc_standard_metrics_class
        self.categorize_difficulty_strategy = categorize_difficulty_class

    def build(self, code: str) -> CodeMetrics:
        if code == "" or code is None:
            raise Exception("Cannot use empty string")
        cm = CodeMetrics()

        standard_metrics = self.calc_standard_metrics_strategy(code).run()

        cm.difficulty = standard_metrics["difficulty"]
        cm.no_of_functions = standard_metrics["no_of_functions"]
        cm.loc = standard_metrics["loc"]
        cm.lloc = standard_metrics["lloc"]
        cm.sloc = standard_metrics["sloc"]
        cm.categorised_difficulty = self.categorize_difficulty_strategy(cm).run()

        tree = ast.parse(code)
        m = CodeAnalysisVisitor()
        m.visit(tree)

        cm.imports = list(m.modules)
        cm.calls = list(m.calls)
        cm.counts = m.counts
        logging.debug(f"MetricsFactory.build: {cm}")

        return cm
