from examon_core.protocols.difficulty import DifficultyProtocol


class DifficultyCategorisor(DifficultyProtocol):
    def __init__(self, metrics) -> None:
        self.metrics = metrics

    def run(self) -> str:
        value = self.metrics.difficulty
        if value == 0:
            return "Easy"
        elif value <= 1:
            return "Medium"
        elif value < 3:
            return "Hard"
        else:
            return "Very Hard"
