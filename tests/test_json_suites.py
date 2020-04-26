import json
import os

import jsonschema

from jsbuilder.builder import JsonSchemaNode
from tests.util import validate

path_json_tests = os.path.join(os.path.dirname(__file__), 'json/tests')


def test_json_suite_draft07():
    path_suite_draft07 = os.path.join(path_json_tests, 'draft-07')
    num_executed = call_tests_in_path(path_suite_draft07)
    print('Executed <{num}> tests'.format(num=num_executed))


def call_tests_in_path(path: str, recursive: bool = True, depth: int = 5):
    if not os.path.exists(path) or not os.path.isdir(path):
        raise ValueError('No such path <{p}>'.format(p=path))

    num_executed = 0
    for filename in os.listdir(path):
        cur_path = os.path.join(path, filename)
        if filename.endswith('.json'):
            num_executed += do_test_json_suite_file(cur_path)
        elif recursive and depth > 0 and os.path.isdir(cur_path):
            num_executed += call_tests_in_path(cur_path, recursive=True, depth=depth-1)

    return num_executed


def do_test_json_suite_file(path: str):
    if not os.path.exists(path) or not os.path.isfile(path):
        raise ValueError('Given json suite file <{p}> is not a file.'.format(p=path))

    with open(path, 'r') as handle:
        json_content = json.load(handle)

    num_tests = 0
    for test_obj in json_content:
        num_tests += execute_test(test_obj)

    return num_tests


def execute_test(test_obj):
    json_description = test_obj['description']
    json_tests = test_obj['tests']
    json_schema = test_obj['schema']

    num_tests = 0
    for t in json_tests:
        if t['valid']:
            node = JsonSchemaNode.from_python(t['data'])
            gen_schema = node.render()
            assert gen_schema is not None
            assert len(gen_schema) > 0
            validate(gen_schema)
            jsonschema.validate(t['data'], gen_schema)
            num_tests += 1

    return num_tests