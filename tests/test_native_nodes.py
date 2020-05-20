import json

from jsbuilder.builder import JsonSchemaObject

from .util import validate


class MyType:
    prop1: int
    prop2: str


def test_empty_object():
    node = JsonSchemaObject()

    schema_instance = node.render()
    assert len(json.dumps(schema_instance)) > 0
    validate(schema_instance)


def test_object_node_from_class():
    node = JsonSchemaObject.from_class(MyType)
    schema_instance = node.render()

    print(json.dumps(node.render(), indent=1))

    validate(schema_instance)
