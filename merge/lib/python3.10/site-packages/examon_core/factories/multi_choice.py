import logging

from examon_core.protocols.multi_choice import MultiChoiceProtocol


class MultiChoiceFactory(MultiChoiceProtocol):
    def __init__(self, correct_answer, choices=None) -> None:
        self.correct_answer = correct_answer
        self.choices = choices

    def build(self):
        if self.correct_answer not in self.choices:
            self.choices.append(self.correct_answer)
        logging.debug(f"MultiChoiceFactory.build: {self.choices}")
        return self.choices
