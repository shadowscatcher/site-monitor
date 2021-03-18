import json


class Serde:
    """
    Common serializer for both consumer and producer
    """
    def __init__(self, encoding='utf-8'):
        self.encoding = encoding

    def serialize(self, value: dict) -> bytes:
        return json.dumps(value).encode(self.encoding)

    def deserialize(self, value: bytes) -> dict:
        return json.loads(value.decode(self.encoding))
