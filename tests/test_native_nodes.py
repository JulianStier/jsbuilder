import json

from jsonschema import validate
from jsbuilder.builder import JsonSchemaObject


draft07_schema_file = 'json/draft-07/schema'
with open(draft07_schema_file, 'r') as handle:
    draft07_schema = json.load(handle)


class MyType():
    prop1: int
    prop2: str


def test_empty_object():
    node = JsonSchemaObject()

    schema_instance = node.render()
    assert len(json.dumps(schema_instance)) > 0
    validate(schema_instance, draft07_schema)


def test_object_node_from_class():
    node = JsonSchemaObject.from_object(MyType)
    schema_instance = node.render()

    print(json.dumps(node.render(), indent=1))

    validate(schema_instance, draft07_schema)
