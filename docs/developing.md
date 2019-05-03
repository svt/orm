# Developer documentation

## Project structure

ORM uses `orm/__main__.py` as entry point which does the following:
- Lists all rule files (according to fileglob argument `--orm-rules-path`).
- Validates rule files.
- Parses rule files into an internal data structure.
- Renders configuration.

### Rule parsing

`orm/parser.py` is:
- Listing rule files
- Parsing rule files into internal data structures.

The internal data structures are fed into the [configuration renderers](#configuration-renderers).

### Rule validation

Rules are validated in `orm/validator.py` by doing:
- YAML syntax validation
- ORM schema validation
- Additional ORM constraints checks

[yamllint](https://pypi.python.org/pypi/yamllint) is used for YAML syntax validation.

ORM schema validation is performed according to versioned schemas in `orm/schemas/`. The [jsonschema](https://pypi.python.org/pypi/jsonschema) python library is used as validator, with [JSON Schema](http://json-schema.org/) [draft 4](https://tools.ietf.org/html/draft-fge-json-schema-validation-00).

Additional ORM constraints, not covererable by prior validations, are specified in `orm/validator.py:validate_rule_constraints`.

### Configuration renderers

Renderers extends the class `RenderOutput` in `orm/render.py`.

Currently there are configuration renderers for HAProxy (`orm/renderhaproxy.py`) and Varnish (`orm/rendervarnish.py`).

### Tests

Unit tests are located in `test/`.

Deployment tests are performed by using the rules and tests in `orm-rules-tests` against the ORM deployment image. HTTP echo servers running in the ORM deployment container are used as backends when needed to verify rule functionality. See the Makefile target `deployment-test` for details.

## Updating ORM dependencies

Run `make list-outdated-deps` to check for candidates.

Edit `install_requires` in `setup.py.in` and run `make update-deps` to generate `requirements.txt`.

## Updating ORM deployment image

The folder `lxd` contains tools for building an ORM deployment, packaged into an LXD image. For more information, see `lxd/README.md`.

## Contributing (developer workflow)

- Fork and create a feature branch.
- Test and implement the new feature.
- Rebase to master.
- Pass tests. `make release-test`
- Document changes in `README.md`, `docs/` and `CHANGELOG.md`
- Create a merge request.
- Let maintainers review changes. +1 required for merge to master.
- Maintainers are responsible for merging.
