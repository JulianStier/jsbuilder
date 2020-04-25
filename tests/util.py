import os
import json
import jsonschema

SCHEMAS = {
    'draft7': {
        'path': 'schemas/draft-07/schema',
        'schema': None
    }
}


def load_schema(name: str) -> dict:
    path_json_resource = os.path.join(os.path.dirname(__file__), 'json')
    if name not in SCHEMAS:
        path_schema_file = os.path.join(path_json_resource, name)
    else:
        if 'schema' in SCHEMAS[name] and SCHEMAS[name]['schema'] is not None:
            return SCHEMAS[name]['schema']
        path_schema_file = os.path.join(path_json_resource, SCHEMAS[name]['path'])

    if not os.path.exists(path_schema_file):
        raise NotImplementedError('No schema path known for given schema <name>'.format(name=name))

    with open(path_schema_file, 'r') as handle:
        schema = json.load(handle)

    if name not in SCHEMAS:
        SCHEMAS[name] = {'path': path_schema_file, 'schema': schema}

    return schema


def validate(instance, schema_name='draft7'):
    schema = load_schema(schema_name)
    return jsonschema.validate(instance, schema)