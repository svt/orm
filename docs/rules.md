# ORM Rules

ORM rule documents (there can be multiple yaml documents in a single file) consists of `rules` and `tests`.

ORM `rules` contain two main parts: _matches_ and _actions_.

_Matches_ are matched against parts of the HTTP requests, such as path, header or query strings, to evaluate if the request should be affected by the rule.

Matches are only omitted when a rule is declared a _Domain default_ rule. The rule then applies to any requests to the domain that are not matched by any other rule.

If a match is made, the corresponding _actions_ are performed. Available actions include path rewriting, header manipulation and backend assignment.

ORM `tests` are user specified tests that can be run during CI jobs (or any mechanism you prefer) in order to verify that the ORM rules give the desired result. Tests are optional.

Please see the [syntax reference](syntax_reference.md) for all available rule parameters. More examples are available in [examples/](../example/README.md) and in the [rule cookbook](rules-cookbook.md).

## Examples

To route requests to `www.example.com` with a path beginning with `/example` (e.g. `curl www.example.com/example/path`) to the origin `https://example-backend.example.com`:

```yaml
---

schema_version: 2

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
