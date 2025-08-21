from typing import List, Type

from examon_core.protocols import CodeExecutionDriverProtocol


class CodeExecutionSandbox:
    def __init__(self, driver_class: Type[CodeExecutionDriverProtocol]) -> None:
        self.driver = driver_class()

    def execute(self, code: str) -> List[str]:
        try:
            self.driver.setup()
            return self.driver.execute(code)
        finally:
            self.driver.teardown()
