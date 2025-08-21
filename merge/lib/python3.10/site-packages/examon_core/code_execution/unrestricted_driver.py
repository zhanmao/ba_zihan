import builtins
import io
from contextlib import redirect_stdout
from typing import List

from examon_core.protocols.code_execution_driver import CodeExecutionDriverProtocol


class UnrestrictedDriver(CodeExecutionDriverProtocol):
    def __init__(self) -> None:
        self.default_print = builtins.print

    def setup(self) -> None:
        builtins.print = self.default_print

    def teardown(self) -> None:
        builtins.print = self.default_print

    def execute(self, code: str) -> List[str]:
        logs = []

        def new_print(*args, **kwargs):
            f = io.StringIO()
            with redirect_stdout(f):
                self.default_print(*args, **kwargs)
            out = f.getvalue().rstrip()
            logs.append(out)
            return None

        builtins.print = new_print
        exec(code)
        return logs
