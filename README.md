# ORM: Origin Routing Machine

ORM performs HTTP routing and rewriting, backed by a user friendly YAML config format called ORM rules with built-in collision detection.

ORM has been running in production at SVT since 2018, handling thousands of requests per second. 16 different teams (and growing) manages their own rules in a shared repository with around 600 rules.

## About

ORM stands for Origin Routing Machine, it's a reverse proxy config generator that manages domains. It uses yaml config files (called ORM rules) to perform specific actions depending on each HTTP request's domain, path and query string.

For example: to route requests to `www.example.com` with a path beginning with `/example` (e.g. `curl www.example.com/example/path`) to the origin `https://example-backend.example.com`:

```yaml
---

schema_version: 1

rules:
  - description: Rule for requests to www.example.com/example
    domains:
      - www.example.com
    matches:
      all:
        - paths:
            begins_with:
              - '/example'
    actions:
      backend:
        origin: 'https://example-backend.example.com'
```

What separates ORM from other reverse proxy services is that rules are written in a standard yaml format which is then converted to configuration files for the proxying services, i.e. HAProxy and Varnish. The rule definitions can then be stored and managed separately from other runtime configuration and rule design does not require knowledge of the configuration file formats for either.

ORM supports HTTP and HTTPS for both incoming requests and for southbound (upstream) requests (to backends).

## Why

The seed that inspired the creation of ORM was the idea of being in control of our own routing rules at SVT. Having a tool like ORM enables one to be CDN agnostic, because there is no need to use proprietary routing and rewriting features.

Another problem we wanted to solve was having multiple teams editing the same ruleset without stepping on each others toes, and being confident that "if I make a change, it will not conflict with or break any other rule in the whole ruleset". The solution to this problem was the ORM rules collision checking that detects if more than one rule can apply logic on the same request. For more info, see [Collision checking](#collision-checking).

## ORM Rules

ORM rule documents (there can be multiple yaml documents in a single file) consists of `rules` and `tests`.

All ORM `rules` contain two main parts: _matches_ and _actions_.

_Matches_ are matched against parts of the HTTP requests, such as path, header or query strings, to evaluate if the request should be affected by the rule. If a match is made, the corresponding _actions_ are performed. Available actions include path rewriting, header manipulation and backend assignment.

ORM `tests` are user specified tests that can be run during CI jobs (or any mechanism you prefer) in order to verify that the ORM rules give the desired result. Tests are optional.

## ORM rule syntax

ORM rule and globals syntax reference is in [docs/syntax_reference.md](docs/syntax_reference.md).

## Collision checking

All rules are checked against each other to verify that no _matches_ overlap. This functionality is a great enabler for having multiple teams work with the same set of ORM rules without the fear of stepping on each others toes.

It's possible to turn off the collision checking, but this will result in unexpected behaviour if any rules should overlap.

When the number of rules starts to grow, the collision checking will take some time. Use the `--cache-path` flag to speed up the process (by avoiding to check rules which have not changed).

## Installing and running ORM

ORM is available as a python `pip` package and as a Docker image.

#### Using the python package:

`pip install origin-routing-machine`

`orm --help`

#### Using the docker image:

`docker run --name orm --rm -v ${PWD}:${PWD} -w ${PWD} -it svtwebcoreinfra/orm --help`

### What happens when I run ORM?

When ORM is run with a path to a ruleset, the rules under the path are:

 * validated and checked for any collisions, i.e. instances of overlapping rules that try to modify the same requests
 * translated into HAProxy and Varnish configuration

### Example

For an example of using ORM with included example rules, and to try it out locally, see [example/README.md](example/README.md).

For a more production-like setup, see the [lxd/](lxd) folder. This deployment is used for the release tests of ORM.

## Building ORM from source

### Dependencies

To build ORM and run the included unit tests the following dependencies are needed:

- make
- python (only tested with python3)
- virtualenv

#### Optional components

`LXD` is needed to build the ORM deployment image and to run the deployment tests.

`docker` is needed to build and distribute the docker images.

### Build python package

In the top directory, run:
```console
foo@bar $ make dist
```

### Build docker images

In the top directory, run:
```console
foo@bar $ make build-docker
```
Two docker images are built, each using a different interpreter: One with `python` and one with `pypy`. The rule validation is much faster with the `pypy` image.

### Build ORM deployment image (LXD)

In the top directory, run:
```console
foo@bar $ make build-orm-deployment
```

## ORM deployment architecture

ORM generates configuration for Varnish and HAProxy. The deployment uses HAProxy as main frontend, listening on HTTP and HTTPS, and performing TLS termination in front of Varnish when HTTPS is used.

All HTTP traffic is then sent to Varnish which handles all rule `matches` and `actions` except `backend`. If the traffic `matches` a rule with a `backend`, Varnish sets a header which identifies the ORM rule, and sends the traffic back to a second, internal HAProxy listener (on a different port).

HAProxy uses the header to perform the `backend` action. For more details, see the deployment example in the `lxd` folder, and examine the generated output from ORM.

### Example deployment schematic

```
             client
              ^ |
              | |
              | V :80 :443
   +-HAProxy-------------+            +-Varnish-----+
   |          ^  \       | HTTP :6081 |             |
   |          |\  - - - -|----------->|- - - -      |
   |          | - - - - -|<-----------|- - no |     |
   |          |          |            |     \ |     |
   |          |          |            |    backend? |
   |          |          |            |       |     |
   |          |          |            |      yes    |
   |          |          | HTTP :4444 |       |     |
   |          |   - - - -|<-----------|- - - -      |
   |          |  /       |            |             |
   +---------------------+            +-------------+
              ^ |
              | | HTTP/HTTPS
              | |
              | V
         #      %    "
      ?    *       !    $
        =   backends  ^   +
      `              ?
        &    #  &      @
```

### Why HAProxy?

A stand-alone Varnish instance can perform most tasks that the ORM array can. So why take the detour through HAProxy?

The reason for including HAProxy in the deployment stems mainly from the fact that:
- Varnish does not support incoming HTTPS traffic
- Varnish (without Plus) does not support HTTPS backends
- HAProxy does load balancing better than Varnish

## Developer documentation

### Project structure

ORM uses `orm/__main__.py` as entry point which does the following:
- Lists all rule files (according to fileglob argument `--orm-rules-path`).
- Validates rule files.
- Parses rule files into an internal data structure.
- Renders configuration.

#### Rule parsing

`orm/parser.py` is:
- Listing rule files
- Parsing rule files into internal data structures.

The internal data structures are fed into the [configuration renderers](#configuration-renderers).

#### Rule validation

Rules are validated in `orm/validator.py` by doing:
- YAML syntax validation
- ORM schema validation
- Additional ORM constraints checks

[yamllint](https://pypi.python.org/pypi/yamllint) is used for YAML syntax validation.

ORM schema validation is performed according to versioned schemas in `orm/schemas/`. The [jsonschema](https://pypi.python.org/pypi/jsonschema) python library is used as validator, with [JSON Schema](http://json-schema.org/) [draft 4](https://tools.ietf.org/html/draft-fge-json-schema-validation-00).

Additional ORM constraints, not covererable by prior validations, are specified in `orm/validator.py:validate_rule_constraints`.

#### Configuration renderers

Renderers extends the class `RenderOutput` in `orm/render.py`.

Currently there are configuration renderers for HAProxy (`orm/renderhaproxy.py`) and Varnish (`orm/rendervarnish.py`).

#### Tests

Unit tests are located in `test/`.

Deployment tests are performed by using the rules and tests in `orm-rules-tests` against the ORM deployment image. HTTP echo servers running in the ORM deployment container are used as backends when needed to verify rule functionality. See the Makefile target `deployment-test` for details.

#### Updating ORM dependencies

Run `make list-outdated-deps` to check for candidates.

Edit `install_requires` in `setup.py.in` and run `make update-deps` to generate `requirements.txt`.

#### Updating ORM deployment image

The folder `lxd` contains tools for building an ORM deployment, packaged into an LXD image. For more information, see `lxd/README.md`.

#### Contributing (developer workflow)

- Fork and create a feature branch.
- Test and implement the new feature.
- Rebase to master.
- Pass tests. `make release-test`
- Document changes in `README.md`, `docs/` and `CHANGELOG.md`
- Create a merge request.
- Let maintainers review changes. +1 required for merge to master.
- Maintainers are responsible for merging.

## Maintainers

- Christian Hernvall https://github.com/splushii
- Frida Hjelm https://github.com/fridahg

## License

[MIT](LICENSE.txt)

## Credits

ORM would not be possible without [HAProxy](http://www.haproxy.org/), [Varnish](https://varnish-cache.org/) and the awesome regular expression library [greenery](https://qntm.org/greenery).
