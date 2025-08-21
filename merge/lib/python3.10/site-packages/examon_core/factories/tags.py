from typing import List

from examon_core.protocols import TagsProtocol


class TagsFactory(TagsProtocol):
    def build(self, _function, _answer, tags: List[str]) -> List[str]:
        return tags
