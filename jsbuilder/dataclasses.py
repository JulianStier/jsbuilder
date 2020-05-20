from dataclasses import _get_field


type_map = {
    str: "string",
    int: "number",
    float: "number",
    dict: "object",
    list: "array",
    bool: "boolean",
}


def to_jsonschema(cls):
    cls_annotations = cls.__dict__.get("__annotations__", {})
    cls_fields = [_get_field(cls, name, type) for name, type in cls_annotations.items()]

    definitions = {}
    properties = {}

    for f in cls_fields:
        descr = {}
        if f.type is None:
            descr["type"] = "null"
        elif f.type in type_map:
            descr["type"] = type_map[f.type]
        else:
            schema = to_jsonschema(f.type)
            definitions[f.name] = schema
            descr["$ref"] = "#/definitions/" + f.name

        properties[f.name] = descr

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "definitions": definitions,
        "properties": properties,
    }
