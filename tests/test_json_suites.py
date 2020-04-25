import json
import os

import jsonschema

from jsbuilder.builder import JsonSchemaNode
from tests.util import validate

path_json_tests = os.path.join(os.path.dirname(__file__), 'json/tests')


def test_json_suite_draft07():
    path_suite_draft07 = os.path.join(path_json_tests, 'draft-07')
    call_tests_in_path(path_suite_draft07)


def call_tests_in_path(path: str, recursive: bool = True, depth: int = 5):
    if not os.path.exists(path) or not os.path.isdir(path):
        raise ValueError('No such path <{p}>'.format(p=path))

    for filename in os.listdir(path):
        cur_path = os.path.join(path, filename)
        if filename.endswith('.json'):
            do_test_json_suite_file(cur_path)
        elif recursive and depth > 0 and os.path.isdir(cur_path):
            call_tests_in_path(cur_path, recursive=True, depth=depth-1)


def do_test_json_suite_file(path: str):
    if not os.path.exists(path) or not os.path.isfile(path):
        raise ValueError('Given json suite file <{p}> is not a file.'.format(p=path))

    with open(path, 'r') as handle:
        json_content = json.load(handle)

    for test_obj in json_content:
        execute_test(test_obj)

def execute_test(test_obj):
    json_description = test_obj['description']
    json_tests = test_obj['tests']
    json_schema = test_obj['schema']

    for t in json_tests:
        if t['valid']:
            node = JsonSchemaNode.from_python(t['data'])
            gen_schema = node.render()
            validate(gen_schema)
            jsonschema.validate(t['data'], gen_schema)