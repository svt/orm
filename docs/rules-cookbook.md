
# ORM Rule Cookbook

 A collection of ORM rule examples and construction principles

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [ORM Rule Cookbook](#orm-rule-cookbook)
  - [1. Matching](#1-matching)
    - [1.1 Path matching strategies](#11-path-matching-strategies)
    - [1.2 Query string matching](#12-query-string-matching)
    - [1.3 HTTP method matching](#13-http-method-matching)
    - [1.4 Negative matching](#14-negative-matching)
    - [1.5 Combining different matching methods](#15-combining-different-matching-methods)
    - [1.6 `domain_default` matching](#16-domaindefault-matching)
  - [2. Actions](#2-actions)
    - [2.1. Routing](#21-routing)
      - [2.1.1 Routing to a single backend](#211-routing-to-a-single-backend)
      - [2.1.2 Balancing over multiple backends](#212-balancing-over-multiple-backends)
      - [2.1.3 Multiple backends with custom queue size and connection limits](#213-multiple-backends-with-custom-queue-size-and-connection-limits)
    - [2.2. Rewriting](#22-rewriting)
      - [2.2.1 Rewriting paths](#221-rewriting-paths)
      - [2.2.2 Rewriting headers](#222-rewriting-headers)
    - [2.3. Redirecting](#23-redirecting)
      - [2.3.1 Simple redirection](#231-simple-redirection)
      - [2.3.2 Redirection with rewriting](#232-redirection-with-rewriting)
      - [2.3.3 Redirection with dynamic rewrite](#233-redirection-with-dynamic-rewrite)
    - [2.4 Synthetic responses](#24-synthetic-responses)
  - [3. Complete examples](#3-complete-examples)
    - [3.1 Routing requests to a single backend and rewriting request headers](#31-routing-requests-to-a-single-backend-and-rewriting-request-headers)
    - [3.2 Routing requests to certain paths to one backend and redirecting everything else](#32-routing-requests-to-certain-paths-to-one-backend-and-redirecting-everything-else)
    - [3.3 Routing requests to different backends based on query parameters](#33-routing-requests-to-different-backends-based-on-query-parameters)
    - [3.4 Redirecting requests to a single URL](#34-redirecting-requests-to-a-single-url)
    - [3.5 Redirecting requests and rewriting the request path](#35-redirecting-requests-and-rewriting-the-request-path)
    - [3.6 Generating a synthetic response, i.e. for domain verification](#36-generating-a-synthetic-response-ie-for-domain-verification)

<!-- /TOC -->

## 1. Matching

### 1.1  Path matching strategies

Match paths that begin with either `/secret/` or `/topsecret/`:

```yaml
  matches:
    all:
      - paths:
          begins_with:
            - '/secret/'
            - '/topsecret/'
```

Match paths that end with `.jpg`:

```yaml
  matches:
    all:
      - paths:
          ends_with:
            - '.jpg'
```

Match paths that either begin with `/images/` OR end with `.jpg`:

```yaml
  matches:
    any:
      - paths:
          begins_with:
            - '/images/'
      - paths:
          ends_with:
            - '.jpg'
```

Match paths that begin with `/images/` AND end with `.jpg`:

```yaml
  matches:
    all:
    - paths:
        begins_with:
          - '/images/'
    - paths:
        ends_with:
          - '.jpg'
```

Match paths that either match one of a list of exact strings or a regex:

```yaml
  matches:
    any:
      - paths:
          regex:
            - '/path/to/matching/directory/.+'
      - paths:
          exact:
            - '/a/very/specific/request/path/'
            - '/another/path/'
            - '/the/last/exact/path/'
```

### 1.2  Query string matching

Match a request based on a specific query string value:

```yaml
  matches:
    any:
      - query:
          exact:
            - 'param=value'
```

Match requests on multiple query strings, case-insensitive on the second matching where the query string can begin with either `param=foo` or `other_param=foo`:

```yaml
  matches:
    any:
      - query:
          exact:
            - 'param=value'
      - query:
          begins_with:
            - 'param=foo'
            - 'other_param=bar'
          ignore_case: true
```

### 1.3  HTTP method matching

Match requests using the POST method:

```yaml
  matches:
    any:
      - method:
          exact:
            - 'POST'
```

Match GET requests to a specific path:

```yaml
  matches:
    all:
      - method:
          exact:
            - 'GET'
      - paths:
          begins_with:
            - '/example/path'
```

### 1.4  Negative matching

Match any paths that are NOT the paths `/public/` or `/html/public/`:

```yaml
  matches:
    all:
      - paths:
          not: True
          begins_with:
            - '/public/'
            - '/html/public/'
```

Match any path that does not END with `/public/`:

```yaml
  matches:
    all:
      - paths:
          not: True
          ends_with:
            - '/public/'
```

### 1.5  Combining different matching methods

Match paths that begin with either `/secret/` or `/topsecret/` EXCEPT the subdirectories `public`:

```yaml
  matches:
    all:
      - paths:
          begins_with:
            - '/secret/'
            - '/topsecret/'
      - paths:
          not: True
          begins_with:
            - '/secret/public/'
            - '/topsecret/public/'
```

As above, but using `ends_with` for negative matching instead:

```yaml
  matches:
    all:
      - paths:
          begins_with:
            - '/secret/'
            - '/topsecret/'
      - paths:
          not: True
          ends_with:
            - '/public/'
```

### 1.6 `domain_default` matching

The `matches` directive can only be present in a rule that does *NOT* have the `domain_default` property set, for obvious reasons. A rule that has `domain_default: True` will match any requests to that domain that are not matched by a rule for the same domain that does explicit matching.

Complete rule example:

```yaml
- description: www.domain.example - domain default
  domains:
    - www.domain.example
  domain_default: True
  actions:
    backend:
      origin: 'https://default-origin.example'
    header_southbound:
      - set:
        field: 'Host'
        value: 'default-origin.example'
      - set:
        field: 'X-Forwarded-Host'
        value: 'www.domain.example'
```

## 2. Actions

### 2.1. Routing

#### 2.1.1 Routing to a single backend

Routes all matched requests to the backend at `https://my-backend.domain.example`:

```yaml
  actions:
    backend:
      origin: 'https://my-backend.domain.example'
```

#### 2.1.2 Balancing over multiple backends

Spreads the matched requests over two servers:

```yaml
  actions:
    backend:
      servers:
        - 'https://backend-1.domain.example'
        - 'https://backend-2.domain.example'
```

#### 2.1.3 Multiple backends with custom queue size and connection limits

```yaml
  actions:
    backend:
      servers:
        - server: 'https://small-backend.domain.example'
          max_connections: 32
          max_queued_connections: 16
        - server: 'https://large-backend.domain.example'
          max_connections: 2048
          max_queued_connections: 1024
```

### 2.2. Rewriting

#### 2.2.1 Rewriting paths

Add a prefix to the request path:

```yaml
  actions:
    req_path:
      - prefix:
          add: /myprefix
```

Replace a specific part of a path regardless of case:

```yaml
  actions:
    req_path:
      - replace:
          from_exact: '/path/to/replace'
          ignore_case: true
          to: '/new/path'
```

Rewrite a path based on regular expression matching:

```yaml
  actions:
    req_path:
      - replace:
          from_regex: '/some/path/(.*)'
          to_regsub: '/\1'
```

The above actually removes the prefix '/some/path' from the path, which can also be achieved using the `prefix` structure:

```yaml
  actions:
    req_path:
      - prefix:
          remove: /some/path
```

#### 2.2.2 Rewriting headers

When manipulating headers, _southbound_ is the direction of the incoming request, i.e. toward the origin, and _northbound_ is the direction of the response, i.e. toward the client.

Setting the southbound host header:

```yaml
  actions:
    header_southbound:
      - set:
          field: 'Host'
          value: 'backend-host-name.domain.example'
```

Adding a southbound header that the backend application requires:

```yaml
  actions:
    header_southbound:
      - add:
          field: 'Authorization'
          value: 'My-secret-authorization-token'
```

Setting various northbound headers for access control:

```yaml
  actions:
    header_northbound:
      - set:
          field: 'Access-Control-Allow-Origin'
          value: '*'
      - set:
          field: 'Access-Control-Allow-Methods'
          value: 'GET,POST'
      - set:
          field: 'Access-Control-Allow-Credentials'
          value: 'false'
      - set:
          field: 'Access-Control-Max-Age'
          value: '86400'
```

Removing a header sent by the origin that should not reach the client:

```yaml
  actions:
    header_northbound:
      - remove: 'X-Robots-Tag'
```

### 2.3. Redirecting

#### 2.3.1 Simple redirection

Temporary (HTTP 307) redirect of all matching requests to a new domain:

```yaml
  actions:
    redirect:
      type: temporary
      domain: www.redirectdomain.example
```

Permanent (HTTP 308) redirect of the same type, but redirect to HTTP specifically:

```yaml
  actions:
    redirect:
      type: permament
      scheme: http
      domain: www.redirectdomain.example
```

Temporary (HTTP 307) redirect of all matching requests to a specific url:

```yaml
  actions:
    redirect:
      type: temporary
      url: https://www.redirectdomain.example/redirected/
```

#### 2.3.2 Redirection with rewriting

Temporarily redirect matching requests to a new domain using HTTPS and adjust the path:

```yaml
  actions:
    redirect:
      type: temporary
      scheme: https
      domain: www.redirectdomain.example
      path:
        - prefix:
            add: /redirected
```

#### 2.3.3 Redirection with dynamic rewrite

Redirection with dynamic rewrite of the path:

```yaml
  actions:
    redirect:
      type: temporary
      path:
        - replace:
            from_regex: /page/(.*).html
            to_regsub: /redirectedpage/\1
```

### 2.4 Synthetic responses

Generating a short synthetic response containing a string:

```yaml
  actions:
    synthetic_response: "Synthetic response body"
```

## 3. Complete examples

### 3.1 Routing requests to a single backend and rewriting request headers

```yaml
rules:
  - description: My production web site
    domains:
      - www.domain.example
    matches:
      all:
        - paths:
            begins_with:
              - '/'
        - paths:
            not: True
            exact:
              - '/xml'
            begins_with:
              - '/xml/'
    actions:
      backend:
        origin: https://my.origin.example
      header_southbound:
        - set:
            field: 'Host'
            value: 'my.origin.example'
        - set:
            field: 'Authorization'
            value: 'example-auth-header-content'
      header_northbound:
        - set:
            field: 'Strict-Transport-Security'
            value: 'max-age=7776000'
        - remove: 'WWW-Authenticate'
```

### 3.2 Routing requests to certain paths to one backend and redirecting everything else

```yaml
rules:
  - description: Domain default rule that redirects requests that do not match any other rule
    domains:
      - www.domain.example
    domain_default: True
    actions:
      redirect:
        type: permanent
        url: https://my.redirect-url.example

  - description: Rule to route requests to a certain path to a backend
    domains:
      - www.mydomain.example
    matches:
      all:
        - paths:
            begins_with:
              - '/non-redirecting-path'
    actions:
      backend:
        origin: https://my.origin.example
      header_southbound:
        - set:
            field: 'Host'
            value: 'my.origin.example'
```

### 3.3 Routing requests to different backends based on query parameters

```yaml
rules:
  - description: Rule to route requests with a specific query string to a separate backend
    domains:
      - www.domain.example
    matches:
      all:
        - query:
            exact:
              - 'special=True'
    actions:
      backend:
        origin: https://special.origin.example
      header_southbound:
        - set:
            field: 'Host'
            value: 'special.origin.example'

  - description: Rule to route requests without a specific query string to another backend
    domains:
      - www.domain.example
    matches:
      all:
        - query:
            not: True
            exact:
              - 'special=True'
    actions:
      backend:
        origin: https://other.origin.example
      header_southbound:
        - set:
            field: 'Host'
            value: 'other.origin.example'
```

### 3.4 Redirecting requests to a single URL

```yaml
rules:
  - description: Redirect www.domain.example to www.redirect-domain.example using https
    domains:
      - www.domain.example
    domain_default: True
    actions:
      redirect:
        type: temporary
        scheme: https
        domain: www.redirect-domain.example
```

### 3.5 Redirecting requests and rewriting the request path

```yaml
rules:
  - description: Redirect domain.example/<path> to www.redirect-domain.example/newlocation/<path>
    domains:
      - domain.example
      - www.domain.example
    domain_default: True
    actions:
      redirect:
        type: temporary
        scheme: https
        domain: www.redirect-domain.example
        path:
          - prefix:
              add: /newlocation
```

### 3.6 Generating a synthetic response, i.e. for domain verification

```yaml
rules:
  - description: Verification challenge response
    domains:
      - domain.example
    matches:
      any:
        - paths:
            exact: /.well-known/domain-verification.txt
    actions:
      synthetic_response: "My_verification_data"
```
