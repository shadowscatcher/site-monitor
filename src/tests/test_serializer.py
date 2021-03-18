from common.serializer import Serde


def test_serializer():
    serializer = Serde()
    val = {
        'some': 'keys',
        'int': 1,
        'bool': True,
        'float': 2.71828,
        'list': []
    }

    decoded, encoded = {'some': 'key'}, b'{"some": "key"}'

    assert serializer.serialize(decoded) == encoded
    assert serializer.deserialize(encoded) == decoded
    assert serializer.deserialize(serializer.serialize(val)) == val
