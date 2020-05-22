from jsbuilder.builder import JsonSchemaNode
from jsbuilder.builder import JsonSchemaObject


class SimpleType:
    prop1: int
    prop2: str


class ComplexType:
    name: str
    sub: SimpleType
    my_list: list
    my_keys: dict


def test_object_nodes_simple_type_equal():
    node1 = JsonSchemaObject.from_class(SimpleType)
    node2 = JsonSchemaObject.from_class(SimpleType)

    assert node1 is not None
    assert node1 == node2


def test_object_nodes_complex_equal():
    node1 = JsonSchemaObject.from_class(ComplexType)
    node2 = JsonSchemaObject.from_class(ComplexType)

    assert node1 is not None
    assert node1 == node2


def test_nodes_from_python_simple_type_equal():
    node1 = JsonSchemaNode.from_python(SimpleType)
    node2 = JsonSchemaNode.from_python(SimpleType)

    assert node1 is not None
    assert node1 == node2


def test_nodes_from_python_complex_type_equal():
    node1 = JsonSchemaNode.from_python(ComplexType)
    node2 = JsonSchemaNode.from_python(ComplexType)

    assert node1 is not None
    assert node1 == node2


def deactivated_test_python_node_object_node_simple_type_equal():
    # TODO this will only hold if we are using the same context if a reference is used ..
    node1 = JsonSchemaNode.from_python(ComplexType)
    node2 = JsonSchemaObject.from_class(ComplexType)

    assert node1 is not None
    assert node1 == node2
