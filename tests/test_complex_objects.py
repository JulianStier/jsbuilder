from jsbuilder.builder import JsonSchemaObject


class SimpleType:
    prop1: int
    prop2: str


class ComplexType:
    name: str
    sub: SimpleType
    my_list: list
    my_keys: dict


def test_nodes_simple_type_equal():
    node1 = JsonSchemaObject.from_object(SimpleType)
    node2 = JsonSchemaObject.from_object(SimpleType)

    assert node1 == node2


def test_nodes_complex_equal():
    node1 = JsonSchemaObject.from_object(ComplexType)
    node2 = JsonSchemaObject.from_object(ComplexType)

    assert node1 == node2

