There are two types of configuration files for ORM, [globals](#orm-globals) and [rules](#orm-rules). Both are written in [YAML](http://yaml.org/). They are versioned by specifying the root key `schema_version`.

### `schema_version`

*integer*

The ORM schema version used in this YAML document. The globals schema is specified in [globals-1.json](../orm/schemas/globals-1.json) (currently `1`) and the rules schema is specified in [rules-2.json](../orm/schemas/rules-2.json) (currently `2`). For a complete reference of all ORM schema versions, refer to the ORM project's [schemata](../orm/schemas/) folder.
 For all supported versions and their schemata, see [schemas.py](../orm/schemas.py).

Values: `1`, `2`

Default: `None`

# ORM regex

ORM uses the same flavour of regex as [greenery](https://github.com/qntm/greenery) (the tool used for collision detection). What can be parsed using the module's `lego.parse` is also allowed as `orm_regex`. For supported syntax and features, see the [greenery docs about regex](https://github.com/qntm/greenery/blob/master/README.md#legoparsestring).

# ORM rules
ORM rules tell ORM what to do with incoming requests. There can be any number of ORM rule files.

## Document root

*object*

| key            | required | type                              |
|----------------|:--------:|-----------------------------------|
| schema_version | ✓        | [schema_version](#schema_version) |
| rules          | ✓        | [rules](#rules)                   |
| tests          |          | [tests](#tests)                   |

## Rules

### `rules`

*array of objects*

Description will be used to generate a unique ID for the rule. It does not need to be unique but it will ease debugging when a unique and concise description is supplied. A rule can be either a regular rule:

| key         | required | type                 |
|-------------|:--------:|----------------------|
| description | ✓        | `string`             |
| domains     | ✓        | [domains](#domains)  |
| matches     | ✓        | [matches](#matches)  |
| actions     | ✓        | [actions](#actions)  |

Or a domain default rule:

| key            | required | type                 |
|----------------|:--------:|----------------------|
| description    | ✓        | `string`             |
| domains        | ✓        | [domains](#domains)  |
| domain_default | ✓        | boolean              |
| actions        | ✓        | [actions](#actions)  |

Domain default rules only take effect if no other rule for the domain matches. There may only be one domain default rule per domain.

### `tests`

### `domains`

*array of [hostname](#hostname)*

Specifies under which domains the rule should have effect. Wildcards are not supported.

Values: E.g. `example.com`, `subdomain.example.com`, etc.

Default: `None`

## Matching
### `matches`

*object*

The rule actions will take effect if the match criterias are satisfied. If `all` **and** `any` is specified, they must both be satisfied. Contains one or both of the following objects:

| key  | required          | type             |
|------|:-----------------:|------------------|
| all  | ✓                 | [all](#all-any)  |

and/or:

| key  | required          | type             |
|------|:-----------------:|------------------|
| any  | ✓                 | [any](#all-any)  |

### `all`, `any`

*array of objects*

all translates to a logical AND for all its elements.
any translates to a logical OR for all its elements.

Contains one or more of the following objects:

| key   | required | type            |
|-------|:--------:|-----------------|
| paths | ✓        | [paths](#paths) |

| key   | required | type            |
|-------|:--------:|-----------------|
| query | ✓        | [query](#query) |

### `paths`

*object*

Used to match against the HTTP request path using the specified matching function(s).

To negate the specified matching function(s), set `not: True`.

To ignore case (i.e. do case insensitive matching), set `ignore_case: True`.

| key         | required | type                        |
|-------------|:--------:|-----------------------------|
| not         |          | boolean (default: false)    |
| ignore_case |          | boolean (default: false)    |
| begins_with | *        | [begins_with](#begins-with) |
| ends_with   | *        | [ends_with](#ends-with)     |
| contains    | *        | [contains](#contains)       |
| exact       | *        | [exact](#exact)             |
| regex       | *        | [regex](#regex)             |

\* At least one matching function is required. Multiple matching functions are allowed.

### `query`

*object*

Used to match against the HTTP request query using the specified matching function(s).

To negate the specified matching function(s), set `not: True`.

To ignore case (i.e. do case insensitive matching), set `ignore_case: True`.

| key         | required | type                        |
|-------------|:--------:|-----------------------------|
| ignore_case |          | boolean (default: false)    |
| not         |          | boolean (default: false)    |
| begins_with | *        | [begins_with](#begins-with) |
| ends_with   | *        | [ends_with](#ends-with)     |
| contains    | *        | [contains](#contains)       |
| exact       | *        | [exact](#exact)             |
| regex       | *        | [regex](#regex)             |

\* At least one matching function is required. Multiple matching functions are allowed.

### `method`

*object*

Used to match against the HTTP request method using the specified matching function(s).

To negate the specified matching function(s), set `not: True`.

To ignore case (i.e. do case insensitive matching), set `ignore_case: True`.

| key         | required | type                        |
|-------------|:--------:|-----------------------------|
| ignore_case |          | boolean (default: false)    |
| not         |          | boolean (default: false)    |
| begins_with | *        | [begins_with](#begins-with) |
| ends_with   | *        | [ends_with](#ends-with)     |
| contains    | *        | [contains](#contains)       |
| exact       | *        | [exact](#exact)             |
| regex       | *        | [regex](#regex)             |

\* At least one matching function is required. Multiple matching functions are allowed.


## Matching functions

### `begins_with`

*array of strings*

Satisfied when the input begins with any of the supplied strings.

Equivalent to the [orm-regex](#orm-regex): `string.*`

### `ends_with`

*array of strings*

Satisfied when the input ends with any of the supplied strings.

Equivalent to the [orm-regex](#orm-regex): `.*string`

### `contains`

*array of strings*

Satisfied when the input contains any of the supplied strings.

Equivalent to the [orm-regex](#orm-regex): `.*string.*`

### `exact`

*array of strings*

Satisfied when the input is an exact match of any of the supplied strings.

Equivalent to the [orm-regex](#orm-regex): `string`

### `regex`

*array of orm_regex*

Satisfied when the input is matched against any of the supplied regular expressions. See [orm-regex](#orm-regex) for reference.

## Actions

### `actions`

*object*

The actions that will be performed if the match criterias are satisfied.

Contains one of the following objects:

| key       | required          | type                  |
|-----------|:-----------------:|-----------------------|
| redirect  | ✓                 | [redirect](#redirect) |

or:

| key               | required | type                                                      |
|-------------------|:--------:|-----------------------------------------------------------|
| backend           |          | [backend](#backend) |
| req_path          |          | [req_path](#req_path) |
| header_southbound |          | [header_southbound](#header_southbound-header_northbound) |
| header_northbound |          | [header_northbound](#header_southbound-header_northbound) |
| trailing_slash    |          | [trailing_slash](#trailing-slash) |

or:

| key                | required | type                                      |
|--------------------|:--------:|-------------------------------------------|
| synthetic_response | ✓        | [synthetic_response](#synthetic-response) |

### `redirect`

*object*

Performs a HTTP redirect. `type` may be either `temporary` (for a HTTP 307 redirect) or `permanent` (for a HTTP 308 redirect).

Contains one of the following objects:

| key  | required | type          |
|------|:--------:|---------------|
| type | ✓        | enum          |
| url  | ✓        | [uri](#uri)   |

The above is used to statically specify the redirect location. The `url` can be absolute or relative. The `Location` header will be set to the value of `url`.

| key    | required | type                              |
|--------|:--------:|-----------------------------------|
| type   | ✓        | enum                              |
| scheme | *        | enum                              |
| domain | *        | [hostname](#hostname)             |
| path   | *        | [string_replace](#string_replace) |

The above is used to only rewrite one (or more) parts of the URL for the redirect location. The parts not specified will be the same as in the original request. For example if we have:
```yaml
redirect:
  type: temporary
  domain: another.domain.example.com
```
The requests *http://example.com/path* and *https://example.com/another/path* will be redirected to *http://another.domain.example.com/path* and *https://another.domain.example.com/another/path* respectively.

`scheme` may be `http` or `https`.

\* At least one of `scheme`, `domain` or `path` must be used.

### `backend`

*object*

Sends the requests to a single origin or loadbalances between multiple servers.

Contains one of the following objects:

| key    | required | type              |
|--------|:--------:|-------------------|
| origin | ✓        | [origin](#origin) |

| key     | required | type                       |
|---------|:--------:|----------------------------|
| servers | ✓        | array of [origin](#origin) |

| key     | required | type                                     |
|---------|:--------:|------------------------------------------|
| servers | ✓        | array of [origin_object](#origin_object) |

### `origin_object`

*object*

Origin object with one or more properties.

Contains one or more of the following objects:

| key                    | required | type                                              |
|------------------------|:--------:|---------------------------------------------------|
| server                 | ✓        | [origin](#origin)                                 |
| max_connections        |          | [max_connections](#max_connections)               |
| max_queued_connections |          | [max_queued_connections](#max_queued_connections) |

### `req_path`

*array of objects*

Modifies the HTTP request path.

Contains one or more of the following objects:

| key     | required | type                              |
|---------|:--------:|-----------------------------------|
| replace | ✓        | [string_replace](#string_replace) |

and/or:

| key     | required | type                              |
|---------|:--------:|-----------------------------------|
| prefix  | ✓        | [string_prefix](#string_prefix)   |

### `header_southbound`, `header_northbound`

*array of objects*

Modifies HTTP headers.

Contains one or more of the following objects:

| key     | required | type                            |
|---------|:--------:|---------------------------------|
| set     | ✓        | [set_header](#set_header)       |

and/or:

| key     | required | type                            |
|---------|:--------:|---------------------------------|
| add     | ✓        | [add_header](#add_header)       |

and/or:

| key     | required | type                            |
|---------|:--------:|---------------------------------|
| remove  | ✓        | [remove_header](#remove_header) |

### `string_replace`

*object*

Replace string content.

Only the first occurrence will be replaced.

To ignore case (i.e. do case insensitive matching), set `ignore_case: True`.

| key         | required | type                      |
|-------------|:--------:|---------------------------|
| ignore_case |          | boolean (default: false)  |
| from_regex  | *        | [orm-regex](#orm-regex)   |
| from_exact  | *        | string                    |
| to          | *        | string                    |
| to_regsub   | *        | [orm-regsub](#orm-regsub) |

\* The allowed combinations are:

|            | from_string | from_regex |
|------------|:-----------:|:----------:|
| to         | ✓           | ✓          |
| to_regsub  |             | ✓          |

### `string_prefix`

*object*

Add and/or remove a prefix from a string.

To ignore case (i.e. do case insensitive matching), set `ignore_case: True`.

| key         | required | type                      |
|-------------|:--------:|---------------------------|
| ignore_case |          | boolean (default: false)  |
| remove      | *        | string                    |
| add         | *        | string                    |

\* At least one of `remove` or `add` must be used. If both are specified, `remove` is performed first, and `add` is performed regardless of whether `remove` made any changes.

### `set_header`

*object*

Set HTTP header field. This will overwrite any previous values.

| key    | required | type                                      |
|--------|:--------:|-------------------------------------------|
| field  | ✓        | [http_header_field_name](#http-header-field-name)   |
| value  | ✓        | [http_header_field_value](#http-header-field-value) |

### `add_header`

*object*

Add HTTP header field. This will append the new value to previous values.

| key    | required | type                                      |
|--------|:--------:|-------------------------------------------|
| field  | ✓        | [http_header_field_name](#http-header-field-name)   |
| value  | ✓        | [http_header_field_value](#http-header-field-value) |

### `remove_header`

*[http_header_field_name](#http-header-field-name)*

Remove HTTP header field.

### `https_redirection`

*boolean*

Redirect HTTP requests to HTTPS.

If set to `true`, ORM will return a HTTP 307 (temporary) redirect with scheme set to https.

Defaults to `false`.

### `trailing_slash`

*enum*

Values: `add`, `remove`, `do_nothing`

Default: `do_nothing`

Adds or removes trailing slashes by using HTTP 307 (temporary) redirects.

If set to `add`, ORM will add trailing slashes to requests. Trailing slashes will only be added when the last part of the HTTP request path begins with a period or does not contain a period. To be precise, the following Varnish regular expression substitution is performed: `regsub(req.url, "^((/[^/]+)*/(\.[^/.]+|[^/.]+))$", "\1/")`

If set to `remove`, ORM will remove trailing slashes from requests. To be precise, the following Varnish regular expression substitution is performed: `regsub(req.url, "^((/[^/]+)*)/$", "\1")`

If set to `do_nothing`, ORM will neither add nor remove trailing slashes from requests.

*This action will be performed before all other actions except [https_redirection](#https-redirection). If a slash needs to be added or removed, a redirection will be performed without any other action having effect. Note that this also means that when coming back to ORM after the redirect, the request may get matched by another ORM rule than the one with the trailing_slash action.*

# ORM globals
ORM globals are used to configure ORM deployment specific settings as well as applying global behaviors that affects all ORM rules. There can only be one ORM globals file.

## Document root

*object*

| key                         | required | type                                    |
|-----------------------------|:--------:|-----------------------------------------|
| schema_version              | ✓        | [schema_version](#schema_version)       |
| crypto                      |          | [crypto](#crypto)                       |
| dns                         |          | [dns](#dns)                             |
| internal_networks           |          | [internal_networks](#internal_networks) |
| defaults                    |          | [defaults](#defaults)                   |
| global_actions              |          | [global_actions](#global_actions)       |
| custom_internal_healthcheck |          | [custom_internal_healthcheck](#custom_internal_healthcheck) |
| haproxy                     |          | [haproxy](#haproxy)                     |
| varnish                     |          | [varnish](#varnish)                     |

## Deployment specific settings

### `crypto`

*object*

Crypto settings.

| key                         | required | type                              |
|-----------------------------|:--------:|-----------------------------------|
| certificates                | ✓        | [certificates](#certificates)     |

### `certificates`

*array of strings*

Paths to PEM files containing both the required certificates and associated private keys.

### `dns`

*object*

DNS settings.

| key                         | required | type                              |
|-----------------------------|:--------:|-----------------------------------|
| nameservers                 | ✓        | [nameservers](#nameservers)       |

### `nameservers`

*array of [hostname_with_port](#hostname_with_port)*

List of DNS nameservers. Port 53 is assumed if unspecified.

### `internal_networks`

*array of [network](#network)*

Specify internal networks to which to lock down specific parts of ORM. Currently, the HAProxy stats page is the only affected part, but it may be possible to specify ORM rules as "internal only" in the future.

### `custom_internal_healthcheck`

*object*

By default in the ORM deployment, the externally facing HAProxy instance uses simple TCP health checks against the Varnish backends. Use this to specifiy a custom health check.

| key                         | required | type                              |
|-----------------------------|:--------:|-----------------------------------|
| http                        | ✓        | [http](#http)                     |

### `haproxy`

*object*

These settings applies to ORM internal machinery, which does not need to be changed in the default setup.

HAProxy is used in ORM to accept requests. It then sends them to Varnish for processing, and then get them back again for loadbalancing to backends. The standard implementation of ORM is to run HAProxy and Varnish on the same host, which means that they will talk to eachother via localhost. But if they are running on separate hosts, you need to configure `address` so Varnish knows where to send back the traffic. You also need to set `address` in [varnish](#varnish). Both defaults to `localhost`.

`user` is the user to run HAProxy as. Defaults to `root`. See http://cbonte.github.io/haproxy-dconv/1.8/configuration.html#3.1-user

`group` is the group to run HAProxy as. Defaults to `root`. See http://cbonte.github.io/haproxy-dconv/1.8/configuration.html#3.1-group

`control_user` is the owner (user) for the HAProxy stats/admin socket. Defaults to `root`. See http://cbonte.github.io/haproxy-dconv/1.8/configuration.html#3.1-group

`control_group` is the group for the HAProxy stats/admin socket. Defaults to `root`. See http://cbonte.github.io/haproxy-dconv/1.8/configuration.html#3.1-group

| key                         | required | type                                      |
|-----------------------------|:--------:|-------------------------------------------|
| address                     | ✓        | [hostname](#hostname)                     |
| user                        | ✓        | [unix_user_or_group](#unix_user_or_group) |
| group                       | ✓        | [unix_user_or_group](#unix_user_or_group) |
| control_user                | ✓        | [unix_user_or_group](#unix_user_or_group) |
| control_group               | ✓        | [unix_user_or_group](#unix_user_or_group) |

### `varnish`

*object*

These settings applies to ORM internal machinery, which does not need to be changed in the default setup.

`address` sets the address of Varnish. Defaults to `localhost`. See the text about `address` at [haproxy](#haproxy) for more information.

| key                         | required | type                                      |
|-----------------------------|:--------:|-------------------------------------------|
| address                     | ✓        | [hostname](#hostname)                     |

### `http`

*object*

Perform a HTTP health check.

`method` defaults to `GET`. Currently only supports `GET`.

| key                         | required | type                              |
|-----------------------------|:--------:|-----------------------------------|
| method                      |          | enum                              |
| domain                      |          | [hostname](#hostname)             |
| path                        | ✓        | [uri-path](#uri-path)             |

## Global behaviors

### `defaults`

*object*

Set defaults for ORM rules. Does **NOT** affect [global_actions](#global_actions).

| key               | required | type                                    |
|-------------------|:--------:|-----------------------------------------|
| https_redirection |          | [https_redirection](#https_redirection) |

### `global_actions`

*object*

Specify actions that are always performed. The actions are performed before the [ORM rules](#orm-rules), both in the northbound and southbound direction.

| key               | required | type                                    |
|-------------------|:--------:|-----------------------------------------|
| https_redirection |          | [https_redirection](#https_redirection) |
| trailing_slash    |          | [trailing_slash](#trailing_slash)       |
| req_path          |          | [req_path](#req_path)                   |
| header_southbound |          | [header_southbound](#header_southbound-header_northbound) |
| header_northbound |          | [header_northbound](#header_southbound-header_northbound) |

# Format types

### max_connections

*integer*

Sets [backend](#backend) [origin_object](#origin_object) maximum number of connections.

Translates into haproxy server [maxconn](https://cbonte.github.io/haproxy-dconv/1.8/configuration.html#5.2-maxconn) parameter

### max_queued_connections

*integer*

Sets [backend](#backend) [origin_object](#origin_object) maximum number of queued connections.

Translates into haproxy server [maxqueue](https://cbonte.github.io/haproxy-dconv/1.8/configuration.html#5.2-maxqueue) parameter.

The queue timeout is 10s.

## http-header-field-name

RFC7230 header field name.

Must match: ```[0-9a-zA-Z!#$%&\'*+\-.^_`|~]+```

## http-header-field-value

RFC7230 header field value.

Must match: `[\u0020-\u007E\t]*`

## orm-regex

See [ORM regex](#orm-regex)

## orm-regsub

The substitution part of a regular expression substitution.

Use `\0` for whole match, `\1` for first capture group, `\2` for second capture group, etc.

## uri-path

RFC3987 IRI/URI path.

## uri-query

RFC3987 IRI/URI query.

## uri

RFC3987 IRI/URI.

## origin

RFC 1123 hostname with optional colon delimited port number and RFC2396 scheme.

Must match: `([a-zA-Z][-+.a-zA-Z0-9]*://)?(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])(:[1-9][0-9]*)?`

## hostname

Uses the JSONSchema python builtin format checker, which at time of writing must satisfy:

`[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}`

## hostname_with_port

RFC 1123 hostname with optional colon delimited port number.

## network

IPv4 address with network mask, e.g. `10.0.0.0/16`.

## unix_user_or_group

A Unix-like user or group. Must satisfy:

`[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)`
