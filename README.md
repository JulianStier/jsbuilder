# Json Schema Builder [![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![Python 3.6](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/) ![Tests](https://github.com/innvariant/jsbuilder/workflows/Tests/badge.svg)




# Related Work
- the official [json-schema](https://json-schema.org/) specification
- [jsonschema](https://github.com/Julian/jsonschema) for python
- [JsonMapping](https://github.com/pudo-attic/jsonmapping)
- the official [semantic versioning "semver"](https://semver.org/) specification



# Development
- install poetry
- Create wheel files in *dist/*: ``poetry build``
- run tests with pytest, e.g. ``poetry run pytest tests/``
- Install wheel in current environment with pip: ``pip install path/to/dist/jsbuilder-0.1.0-py3-none-any.whl``

### Running CI image locally
Install latest *gitlab-runner* (version 12.3 or up):
```bash
# For Debian/Ubuntu/Mint
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash

# For RHEL/CentOS/Fedora
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh | sudo bash

apt-get update
apt-get install gitlab-runner

$ gitlab-runner -v
Version:      12.3.0
```
Execute job *tests*: ``gitlab-runner exec docker test-python3.6``

### Running pre-commit hook locally
``poetry run pre-commit run --all-files``

### Running github action locally
Install *https://github.com/nektos/act*.
Run ``act``
