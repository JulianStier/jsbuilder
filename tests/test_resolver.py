from jsbuilder.builder import DefaultJsonSchemaResolver, JsonSchemaResolver, ObjectJsonSchemaResolver
from jsbuilder.builder import JsonSchemaArray
from jsbuilder.builder import JsonSchemaInteger
from jsbuilder.builder import JsonSchemaNumber
from jsbuilder.builder import JsonSchemaObject
from jsbuilder.builder import JsonSchemaString


def test_dev():
    schema = {
        "$id": "",
        "definitions": {
            "my_arr": {"type": "array", "minItems": 1, "items": {"$ref": "#"}}
        },
    }
    resolver = ObjectJsonSchemaResolver("", schema)

    with resolver.in_scope("schemaArray"):
        resolver.resolve("a")


def test_resolve_array():
    schema = {
        "$id": "",
        "definitions": {
            "my_arr": {"type": "array", "minItems": 1, "items": {"$ref": "#"}}
        },
    }
    resolver = ObjectJsonSchemaResolver("", schema)
    node = resolver.resolve("my_arr")  # schema->RefNode[/definitions/my_arr]
    print(node)


def test_default_string_resolves_to_stringnode():
    resolver = DefaultJsonSchemaResolver.get_instance()
    resolved_node = resolver.resolve("str")

    assert resolved_node == JsonSchemaString()


def test_default_float_resolves_to_numbernode():
    resolver = DefaultJsonSchemaResolver.get_instance()
    resolved_node = resolver.resolve(5.0)

    assert resolved_node == JsonSchemaNumber()


def test_default_int_resolves_to_integernode():
    resolver = DefaultJsonSchemaResolver.get_instance()
    resolved_node = resolver.resolve(5)

    assert resolved_node == JsonSchemaInteger()


def test_default_array_resolves_to_arraynode():
    resolver = DefaultJsonSchemaResolver.get_instance()
    resolved_node = resolver.resolve([])

    assert resolved_node == JsonSchemaArray()


def test_default_dict_resolves_to_objectnode():
    resolver = DefaultJsonSchemaResolver.get_instance()
    resolved_node = resolver.resolve({})

    assert resolved_node == JsonSchemaObject()
