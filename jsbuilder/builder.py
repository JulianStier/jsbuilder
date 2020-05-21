import contextlib
import functools
import inspect
import json
import urllib.parse

from dataclasses import _get_field
from typing import List


def resolve_id(schema):
    if schema is True or schema is False:
        return u""
    return schema.get(u"$id", u"")


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
    str: NativeJsonschemaTypes.string,
    int: NativeJsonschemaTypes.number,
    float: NativeJsonschemaTypes.number,
    dict: NativeJsonschemaTypes.object,
    list: NativeJsonschemaTypes.array,
    bool: NativeJsonschemaTypes.boolean,
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
    elif hasattr(unknown_type, "__name__"):
        return JsonSchemaRef(getattr(unknown_type, "__name__"))

    return None


class JsonSchemaResolver:
    def __init__(self, base_uri: str, reference=None, fn_urljoin=None):
        self._scope_stack = [base_uri]
        self._reference = reference

        if fn_urljoin is None:
            fn_urljoin = functools.lru_cache(1024)(urllib.parse.urljoin)
        self._urljoin = fn_urljoin

    @property
    def scope(self):
        return self._scope_stack[-1]

    def push_scope(self, scope: str):
        self._scope_stack.append(self._urljoin(self.scope, scope))

    def pop_scope(self):
        try:
            self._scope_stack.pop()
        except IndexError:
            # TODO probably introduce own error hierarchy
            raise ValueError(
                "Failed to pop the scope from an empty stack. "
                "`pop_scope()` should only be called once for every "
                "`push_scope()`"
            )

    @contextlib.contextmanager
    def in_scope(self, scope: str):
        self.push_scope(scope)
        try:
            yield
        finally:
            self.pop_scope()

    @contextlib.contextmanager
    def resolving(self, ref: str):
        url, resolved = self.resolve(ref)
        self.push_scope(url)
        try:
            yield resolved
        finally:
            self.pop_scope()

    def resolve(self, descr):
        raise NotImplementedError()


class ObjectJsonSchemaResolver(JsonSchemaResolver):
    def __init__(self, base_uri: str, schema):
        super().__init__(base_uri)

    def resolve(self, descr):
        pass


class JsonSchemaChainedResolver(JsonSchemaResolver):
    def __init__(self, base_uri: str, resolvers: List[JsonSchemaResolver]):
        super().__init__(base_uri)
        self._chain_resolvers = resolvers

    def __radd__(self, other):
        if not isinstance(other, JsonSchemaResolver):
            raise ValueError("Can only add JsonSchemaResolver to chain.")
        self.add_resolver(other)

    def resolve(self, descr):
        for resolver in self._chain_resolvers:
            node = resolver.resolve(descr)
            if node is not None:
                return node
        return None

    def add_resolver(self, resolver: JsonSchemaResolver):
        self._chain_resolvers.append(resolver)


class DefaultJsonSchemaResolver(JsonSchemaResolver):
    @classmethod
    def get_instance(cls):
        CLS_KEY_INSTANCE = "__default_resolver"
        if not hasattr(cls, CLS_KEY_INSTANCE):
            # TODO this instantiation is deprecated
            setattr(cls, CLS_KEY_INSTANCE, cls(base_uri=""))
        return getattr(cls, CLS_KEY_INSTANCE)

    def resolve(self, unknown_type):
        resolved = _resolve_node(unknown_type)
        if resolved is not None:
            return resolved

        # Given object is a complex class or an exemplary object
        # TODO use object to resolve
        if hasattr(unknown_type, "__annotations__"):
            return JsonSchemaObject.from_class(unknown_type)

        if hasattr(unknown_type, "__name__"):
            return JsonSchemaRef(getattr(unknown_type, "__name__"))

        native_type = type(unknown_type)
        node = self.resolve(native_type)
        # TODO node set default

        return node


class JsonSchemaNode(object):
    _resolver: JsonSchemaResolver = None

    @classmethod
    def from_python(cls, obj):
        return DefaultJsonSchemaResolver.get_instance().resolve(obj)

    @property
    def resolver(self):
        return (
            self._resolver
            if self._resolver is not None
            else DefaultJsonSchemaResolver.get_instance()
        )

    @resolver.setter
    def resolver(self, resolver: JsonSchemaResolver):
        self._resolver = resolver

    def render(self):
        raise NotImplementedError("Base class does not implement rendering.")

    def is_native(self):
        return False

    def __str__(self):
        return json.dumps(self.render())


class JsonSchemaNull(JsonSchemaNode):
    def render(self):
        return {"type": "null"}

    def is_native(self):
        return True


class JsonSchemaRef(JsonSchemaNode):
    def __init__(self, ref_name: str, root: str = "#/definitions/"):
        self._root = root
        self._ref_name = ref_name

    def render(self):
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
        raise TypeError(
            "Could not find complex type <T> without schema context.".format(
                T=unknown_type
            )
        )

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
    def from_class(schema_class, cls):
        assert inspect.isclass(cls)
        cls_annotations = cls.__dict__.get("__annotations__", {})
        cls_fields = [
            _get_field(cls, name, type) for name, type in cls_annotations.items()
        ]

        schema_obj = schema_class()
        for f in cls_fields:
            schema_obj.add_property(f.name, f.type)
            # print(f)

        return schema_obj

    def __init__(self, properties: list = None):
        self._properties = properties or {}

    """def add_property(self, name, raw_type):
        type_node = _resolve_node(raw_type)
        if type_node is None:
            # TODO resolve name
            if hasattr(raw_type, '__name__'):
                type_name = str(raw_type.__name__)
            else:
                type_name = type(raw_type).__name__
            type_node = JsonSchemaRef(type_name)
        self._properties[name] = type_node"""

    def add_property(self, name, raw_type):
        self._properties[name] = self.resolver.resolve(raw_type)

    def render(self):
        descr = {"type": "object"}

        descr_properties = {}
        for prop_name in self._properties:
            descr_properties[prop_name] = self._properties[prop_name].render()
        if len(descr_properties) > 0:
            descr["properties"] = descr_properties

        return descr

    def is_native(self):
        return all(
            self._properties[prop_name].is_native()
            if isinstance(self._properties[prop_name], JsonSchemaNode)
            else self._properties[prop_name] in native_jsonschema_types
            for prop_name in self._properties
        )

    def __eq__(self, other):
        if not isinstance(other, JsonSchemaObject):
            return False

        if len(self._properties) != len(other._properties):
            return False

        for p_name in self._properties:
            if self._properties[p_name] != other._properties[p_name]:
                return False

        return True


class JsonSchemaArray(JsonSchemaNode):
    def render(self):
        return {"type": "array"}

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

    def render(self):
        descr = {"type": self._exact_type}
        if self._multiple_of is not None:
            descr["multipleOf"] = self._multiple_of
        return descr

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaNumber)


class JsonSchemaInteger(JsonSchemaNode):
    def render(self):
        return {"type": "integer"}

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaInteger)


class JsonSchemaString(JsonSchemaNode):
    def render(self):
        return {"type": "string"}

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaString)


class JsonSchemaBoolean(JsonSchemaNode):
    def render(self):
        return {"type": "boolean"}

    def is_native(self):
        return True

    def __eq__(self, other):
        return isinstance(other, JsonSchemaBoolean)


native_jsonschema_map = {
    NativeJsonschemaTypes.string: JsonSchemaString(),
    NativeJsonschemaTypes.number: JsonSchemaNumber(),
    NativeJsonschemaTypes.object: JsonSchemaObject(),
    NativeJsonschemaTypes.array: JsonSchemaArray(),
    NativeJsonschemaTypes.boolean: JsonSchemaBoolean(),
}


class JsonSchemaBuilder(JsonSchemaObject):
    _DEFAULT_URI = "http://json-schema.org/draft-07/schema#"

    def __init__(self, schema_uri: str = None):
        super().__init__()
        self._schema_uri = (
            schema_uri if schema_uri is not None else JsonSchemaBuilder._DEFAULT_URI
        )
        self._properties = {}
        self._definitions = {}
        self.resolver = JsonSchemaChainedResolver(
            schema_uri,
            [
                JsonSchemaBuilderResolver(schema_uri, self),
                DefaultJsonSchemaResolver.get_instance(),
            ],
        )

    def render(self):
        descr = {}
        descr["$schema"] = self._schema_uri
        descr["type"] = "object"

        descr_props = {}
        for prop_name in self._properties:
            node = self._properties[prop_name]
            assert isinstance(
                node, JsonSchemaNode
            ), "Property nodes should have been translated to node objects."
            node.resolver = self.resolver
            descr_props[prop_name] = node.render()

        descr_defs = {}
        for def_name in self._definitions:
            node = self._definitions[def_name]
            assert isinstance(
                node, JsonSchemaNode
            ), "Property nodes should have been translated to node objects."
            node.resolver = self.resolver
            descr_defs[def_name] = node.render()

        descr["definitions"] = descr_defs
        descr["properties"] = descr_props
        return descr

    def add_definition(self, type_name, raw_type):
        type_obj = JsonSchemaObject.from_class(raw_type)
        if type_name in self._definitions and self._definitions[type_name] != type_obj:
            raise TypeError(
                "You already have added a definition for <T> but it was different: <A> != <B>".format(
                    T=type_name, A=self._definitions[type_name], B=type_obj
                )
            )
        self._definitions[type_name] = type_obj


class JsonSchemaBuilderResolver(JsonSchemaResolver):
    _refs = set()
    _python_type_to_ref_map = {}
    _refs_to_nodes = {}

    def __init__(self, base_uri: str, builder: JsonSchemaBuilder):
        super().__init__(base_uri)
        self._builder = builder

    def resolve(self, descr):
        if isinstance(descr, JsonSchemaNode):
            if descr.is_native():
                return descr
            else:
                ref = self._find_ref_by_node(descr)
                return ref

        if descr in self._python_type_to_ref_map:
            return self._python_type_to_ref_map[descr]

        node = DefaultJsonSchemaResolver.get_instance().resolve(descr)
        if isinstance(node, JsonSchemaObject):
            ref_name = descr.__name__
            node_ref = JsonSchemaRef(ref_name)
            self._python_type_to_ref_map[descr] = node_ref
            self._refs_to_nodes[ref_name] = node
            self._builder.add_definition(ref_name, descr)

            print("Got description <{descr}>".format(descr=descr))
            print("Resolved to <{resolve}>".format(resolve=node))
            print("Created ref_name <{ref_name}>".format(ref_name=ref_name))
            return node_ref

        return node

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
