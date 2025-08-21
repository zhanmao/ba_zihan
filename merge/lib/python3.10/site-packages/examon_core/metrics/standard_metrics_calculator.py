from examon_core.protocols.code_metrics import CodeMetricsProtocol
from radon.metrics import h_visit
from radon.raw import analyze


class StandardMetricsCalculator(CodeMetricsProtocol):
    def __init__(self, code: str) -> None:
        self.code = code

    def run(self) -> dict[str, float]:
        raw = analyze(self.code)
        visit_data = h_visit(self.code)
        return {
            "difficulty": round(visit_data.total.difficulty, 2),
            "no_of_functions": len(visit_data.functions),
            "loc": raw.loc,
            "lloc": raw.lloc,
            "sloc": raw.sloc,
        }
