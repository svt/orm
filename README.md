# ORM: Origin Routing Machine

## What it is

ORM is a reverse proxy configuration generator. It generates configuration for HAProxy and Varnish to perform HTTP routing and rewriting, backed by a user friendly YAML config format called ORM rules with built-in collision detection.

ORM has been used in production at SVT since 2018, handling thousands of requests per second. 16 different teams (and growing) manages their own rules in a shared repository with around 600 rules.

Have a look at our [deployment example](example/README.md) to get started running ORM yourself!

## How it works

ORM manages routing configuration based on rules defined in yaml format. It uses yaml config files (referred to as ORM rules) to produce specific actions depending on each HTTP request's domain, path and query string. To route requests to `www.example.com` with a path beginning with `/example` (e.g. `curl www.example.com/example/path`) to the origin `https://example-backend.example.com`:

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
Rules are written in a standard yaml format which is then converted to configuration files for the proxying services, i.e. HAProxy and Varnish. The rule definitions can then be stored and managed separately from other runtime configuration and rule design does not require knowledge of the configuration file formats for either.

ORM supports HTTP and HTTPS for both incoming requests and for southbound (upstream) requests (to backends).

## Who is ORM for?

The seed that inspired the creation of ORM was the idea of letting DevOps teams control their own routing rules without having to edit software-specific configuration, much like some CDN:s allow. Having a tool like ORM enables one to be CDN agnostic, because there is no need to use proprietary routing and rewriting features.

We also wanted to let multiple teams edit the same ruleset without stepping on each others toes without worrying that changes would affect other rules in the ruleset. The ORM rules collision checking detects if more than one rule can apply logic on the same request, safeguarding against such collisions - for more info, see [docs/collision_checking.md](docs/collision_checking.md).

If you need a tool to help you manage rulesets for reverse proxying without having to learn software-specific configuration syntax, then ORM is for you.

## Learn more

* [Writing rules](docs/rules.md)
* [Installing & running](docs/running.md)
* [Collision checking](docs/collision_checking.md)
* [Deploying](docs/deploying.md)
* [Developing](docs/developing.md)
* [Building](docs/building.md)
* [Syntax reference](docs/syntax_reference.md)

## Contributing

We welcome code contributions as well as questions, suggestions, feature requests, bug reports, other feedback and success stories alike. Please feel free to open an issue in the main repo at https://github.com/SVT/orm to start the conversation. Contribution guidelines and workflow are available in the [Developer docs](docs/developing.md)

## Maintainers

- Christian Hernvall https://github.com/splushii
- Frida Hjelm https://github.com/svtfrida

## License

[MIT](LICENSE.txt)

## Credits

ORM would not be possible without [HAProxy](http://www.haproxy.org/), [Varnish](https://varnish-cache.org/) and the awesome regular expression library [greenery](https://qntm.org/greenery).
