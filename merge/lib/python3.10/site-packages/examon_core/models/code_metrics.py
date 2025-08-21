from dataclasses import dataclass


@dataclass
class CodeMetrics:
    no_of_functions: int = None
    loc: int = None
    lloc: int = None
    sloc: int = None
    difficulty: float = None
    categorised_difficulty: str = None
    imports: list[str] = None
    calls: list[str] = None
    counts: dict[str, int] = None

    def __repr__(self) -> str:
        return (
            f"CodeMetrics(difficulty: {self.difficulty},"
            f"no_of_functions: {self.no_of_functions}, "
            f"loc: {self.loc}, "
            f"lloc: {self.lloc}, "
            f"sloc: {self.sloc}, "
            f"difficulty: {self.difficulty}, "
            f"categorised_difficulty: {self.categorised_difficulty}, "
            f"imports: {self.imports}, "
            f"calls: {self.calls}, "
            f"counts: {self.counts})"
        )
