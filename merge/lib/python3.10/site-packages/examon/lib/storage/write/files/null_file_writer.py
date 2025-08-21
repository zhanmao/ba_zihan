from ..protocols import FileWriter


class NullFileDriver(FileWriter):
    def __init__(self, _filename_strategy=None, _models: list = None):
        ...

    def create_files(self) -> None:
        ...

    def delete_files(self) -> None:
        ...
