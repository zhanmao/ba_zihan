import hashlib

from examon_core.protocols.unique_id import UniqueIdProtocol


class UniqueIdGenerator(UniqueIdProtocol):
    def run(self, function_src) -> str:
        m = hashlib.md5()
        m.update(function_src.encode())
        return str(int(m.hexdigest(), 16))[0:32]
