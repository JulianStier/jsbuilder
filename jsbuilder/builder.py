import inspect
from dataclasses import _get_field
from typing import List


class NativeJsonschemaTypes:
    string = "string"
    number = "number"
    object = "object"
    array = "array"
    boolean = "boolean"


native_jsonschema_types = [
    NativeJsonschemaTypes.string,
    NativeJsonschemaTypes.number,
    NativeJsonschemaTypes.object,
    NativeJsonschemaTypes.array,
    NativeJsonschemaTypes.boolean,
]

python_type_map = {
    str: "string",
    int: "number",
    float: "number",
    dict: "object",
    list: "array",
    bool: "boolean"
}


def _resolve_node(unknown_type):
    if unknown_type is None:
        return JsonSchemaNull()
    elif unknown_type is str:
        if unknown_type in native_jsonschema_map:
            return native_jsonschema_map[unknown_type]
        return JsonSchemaString()
    elif unknown_type is bool:
        return JsonSchemaBoolean()
    elif unknown_type is int:
        return JsonSchemaInteger()
    elif unknown_type is float:
        return JsonSchemaNumber()
    elif unknown_type is dict:
        return JsonSchemaObject()
    elif unknown_type is list:
        return JsonSchemaArray()

    return None


class JsonSchemaResolver():
    def resolve(self, descr):
        raise NotImplementedError()


class JsonSchemaNode(object):
    @classmethod
    def from_python(cls, obj):
        node = _resolve_node(obj)
        if node is None:
            node = _resolve_node(type(obj))
        return node

    def render(self, resolver: JsonSchemaResolver = None):
        raise NotImplementedError('Base class does not implement rendering.')

    def is_native(self):
        return False


class JsonSchemaNull(JsonSchemaNode):
    def render(self, resolver: JsonSchemaResolver = None):
        return {"type": "null"}

    def is_native(self):
        return True


class JsonSchemaRef(JsonSchemaNode):
    def __init__(self, ref_name: str, root: str='#/definitions/'):
        self._root = root
        self._ref_name = ref_name

    def render(self, resolver: JsonSchemaResolver = None):
        return {"$ref": self._root + self._ref_name}

    def is_native(self):
        return False

    def __eq__(self, other):
        if not isinstance(other, JsonSchemaRef):
            return False

        return self._root == other._root and self._ref_name == other._ref_name


def _find_ref_node_in_defs(unknown_type, definitions: dict) -> (JsonSchemaRef, None):
    for d_name in definitions:
        d = definitions[d_name]
        if unknown_type == d:
            return JsonSchemaRef(d_name)
    return None


def _find_ref_node_in_schema(unknown_type, schema_context) -> (JsonSchemaRef, None):
    if schema_context is None or "definitions" not in schema_context:
        raise TypeError('Could not find complex type <T> without schema context.'.format(T=unknown_type))

    return _find_ref_node_in_defs(unknown_type, schema_context["definitions"])


class JsonSchemaObject(JsonSchemaNode):
    @classmethod
    def from_dict(cls, d: dict):
        schema_obj = cls()
        for p_name in d:
            p_val = d[p_name]
            schema_obj.add_property(p_name, p_val)
        return schema_obj

    @classmethod
    def from_object(schema_class, cls):
        assert inspect.isclass(cls)
        cls_annotations = cls.__dict__.get('__annotations__', {})
        cls_fields = [_get_field(cls, name, type) for name, type in cls_annotations.items()]

        schema_obj = schema_class()
        for f in cls_fields:
            schema_obj.add_property(f.name, f.type)
            #print(f)

        return schema_obj

    def __init__(self, properties: list = None):
        self._properties = properties or {}

    def add_property(self, name, raw_type):
        type_node = _resolve_node(raw_type)
        if type_node is None:
            # TODO resolve name
            if hasattr(raw_type, '__name__'):
                type_name = str(raw_type.__name__)
            else:
                type_name = type(raw_type).__name__
            type_node = JsonSchemaRef(type_name)
        self._properties[name] = type_node

    def render(self, resolver: JsonSchemaResolver = None):
        descr = {"type": "object"}

        descr_properties = {}
        for prop_name in self._properties:
            node = self._properties[prop_name]

            if resolver is not None:
                resolved_node = resolver.resolve(node)
                descr_properties[prop_name] = resolved_node.render()
            elif isinstance(node, JsonSchemaNode):
                descr_properties[prop_name] = self._properties[prop_name].render()
            elif node in python_type_map:
                descr_properties[prop_name] = {"type": python_type_map[node]}
        if len(descr_properties) > 0:
            descr["properties"] = descr_properties

        return descr

    def is_native(self):
        return all(self._properties[prop_name].is_native() if isinstance(self._properties[prop_name], JsonSchemaNode) else self._properties[prop_name] in native_jsonschema_types for prop_name in self._properties)

    def __eq__(self, other):
        if not isinstance(other, JsonSchemaObject):
            return False

        if len(self._properties) != len(other._properties):
            return False

        for p_name in self._properties:
            if self._properties[p_name] != other._properties[p_name]:
                return False

        return True

    def __str__(self):
        return self.render()


class JsonSchemaArray(JsonSchemaNode):
    def render(self, resolver: JsonSchemaResolver = None):
        return {
            "type": "array"
        }

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaArray) or other == list


class JsonSchemaNumber(JsonSchemaNode):
    def __init__(self, exact_type: str = None, multipleOf: int = None):
        self._exact_type = exact_type if exact_type is not None else "number"
        assert self._exact_type in ["integer", "number"]
        if multipleOf is not None:
            assert multipleOf > 0  # must be a positive number
        self._multiple_of = multipleOf

    def render(self, resolver: JsonSchemaResolver = None):
        descr = { "type": self._exact_type }
        if self._multiple_of is not None:
            descr["multipleOf"] = self._multiple_of
        return descr

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaNumber)


class JsonSchemaInteger(JsonSchemaNode):
    def render(self, resolver: JsonSchemaResolver = None):
        return {
            "type": "integer"
        }

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaInteger)


class JsonSchemaString(JsonSchemaNode):
    def render(self, resolver: JsonSchemaResolver = None):
        return {
            "type": "string"
        }

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaString)


class JsonSchemaBoolean(JsonSchemaNode):
    def render(self):
        return {
            "type": "boolean"
        }

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaBoolean)


native_jsonschema_map = {}
native_jsonschema_map[NativeJsonschemaTypes.string] = JsonSchemaString()
native_jsonschema_map[NativeJsonschemaTypes.number] = JsonSchemaNumber()
native_jsonschema_map[NativeJsonschemaTypes.object] = JsonSchemaObject()
native_jsonschema_map[NativeJsonschemaTypes.array] = JsonSchemaArray()
native_jsonschema_map[NativeJsonschemaTypes.boolean] = JsonSchemaBoolean()


class JsonSchemaBuilder(object):
    _DEFAULT_URI = 'http://json-schema.org/draft-07/schema#'

    def __init__(self, schema_uri: str=None):
        self._schema_uri = schema_uri if schema_uri is not None else JsonSchemaBuilder._DEFAULT_URI
        self._properties = {}
        self._definitions = {}

    def render(self):
        resolver = JsonSchemaBuilderResolver(self)

        descr = {}
        descr["$schema"] = self._schema_uri
        descr["type"] = "object"

        descr_props = {}
        for prop_name in self._properties:
            node = self._properties[prop_name]
            assert isinstance(node, JsonSchemaNode), 'Property nodes should have been translated to node objects.'
            descr_props[prop_name] = node.render(resolver)

        descr_defs = {}
        for def_name in self._definitions:
            node = self._definitions[def_name]
            assert isinstance(node, JsonSchemaNode), 'Property nodes should have been translated to node objects.'
            descr_defs[def_name] = node.render()

        descr["definitions"] = descr_defs
        descr["properties"] = descr_props
        return descr

    def add_property(self, name, raw_type):
        type_node = _resolve_node(raw_type)
        if type_node is None:
            type_ref = _find_ref_node_in_defs(raw_type, self._definitions)
            if type_ref is None:
                # TODO resolve name
                type_name = str(raw_type.__name__)
                self.add_definition(type_name, raw_type)
                type_ref = JsonSchemaRef(type_name)
            type_node = type_ref
        self._properties[name] = type_node

    def add_definition(self, type_name, raw_type):
        type_obj = JsonSchemaObject.from_object(raw_type)
        if type_name in self._definitions and self._definitions[type_name] != type_obj:
            raise TypeError('You already have added a definition for <T> but it was different: <A> != <B>'.format(T=type_name, A=self._definitions[type_name], B=type_obj))
        self._definitions[type_name] = type_obj


class JsonSchemaBuilderResolver(JsonSchemaResolver):
    _refs = {}

    def __init__(self, builder: JsonSchemaBuilder):
        self._builder = builder

    def resolve(self, descr):
        if isinstance(descr, JsonSchemaNode):
            if descr.is_native():
                return descr
            else:
                ref = self._find_ref_by_node(descr)
                return ref

    def _find_ref_by_name(self, name) -> (JsonSchemaRef, None):
        for d in self._builder._definitions:
            if d == name:
                return JsonSchemaRef(d)
        return None

    def _find_ref_by_node(self, node: JsonSchemaNode) -> (JsonSchemaRef, None):
        for d in self._builder._definitions:
            if self._builder._definitions[d] == node:
                return JsonSchemaRef(d)
        return None
