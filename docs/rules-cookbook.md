<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [ORM Rule Cookbook](#orm-rule-cookbook)
	- [1. Matching](#1-matching)
		- [1.1  Path matching strategies](#11-path-matching-strategies)
		- [1.2  Query parameter matching](#12-query-parameter-matching)
		- [1.3  Negative matching](#13-negative-matching)
		- [1.4  Combining different matching methods](#14-combining-different-matching-methods)
		- [1.5 `domain_default` matching](#15-domaindefault-matching)
	- [2. Actions](#2-actions)
		- [2.1. Routing](#21-routing)
			- [2.1.1 Routing to a single backend](#211-routing-to-a-single-backend)
			- [2.1.2 Balancing over multiple backends](#212-balancing-over-multiple-backends)
			- [2.1.3 Multiple backends with custom queue size and connection limits:](#213-multiple-backends-with-custom-queue-size-and-connection-limits)
		- [2.2. Rewriting](#22-rewriting)
			- [2.2.1 Rewriting paths](#221-rewriting-paths)
			- [2.2.2 Rewriting headers](#222-rewriting-headers)
		- [2.3. Redirecting](#23-redirecting)
			- [2.3.1 Simple redirection](#231-simple-redirection)
			- [2.3.2 Redirection with rewriting](#232-redirection-with-rewriting)
	- [3. Complete examples](#3-complete-examples)
		- [3.1 Routing requests to a single backend and rewriting request headers](#31-routing-requests-to-a-single-backend-and-rewriting-request-headers)
		- [3.2 Routing requests to certain paths to one backend and redirecting everything else](#32-routing-requests-to-certain-paths-to-one-backend-and-redirecting-everything-else)
		- [3.3 Routing requests to different backends based on query parameters](#33-routing-requests-to-different-backends-based-on-query-parameters)
		- [3.4 Redirecting requests to a single URL](#34-redirecting-requests-to-a-single-url)
		- [3.5 Redirecting requests and rewriting the request path](#35-redirecting-requests-and-rewriting-the-request-path)

<!-- /TOC -->

# ORM Rule Cookbook
 A collection of ORM rule examples and construction principles

## 1. Matching

### 1.1  Path matching strategies

Match paths that begin with either `/secret/` or `/topsecret/`:
```
  matches:
    all:
      - paths:
          begins_with:
            - '/secret/'
            - '/topsecret/'
```


Match paths that end with `.jpg`:
```
  matches:
    all:
      - paths:
          ends_with:
            - '.jpg'
```

Match paths that either begin with `/images/` OR end with `.jpg`:
```
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
```
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

```
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

### 1.2  Query parameter matching

Match a request based on a specific value for a parameter:

```
  matches:
    any:
      - query:
          parameter: my_parameter
          exact:
            - required_value
```

Match requests on multiple parameters, case-insensitive on the second parameter which can begin with either `foo` or `bar`:

```
  matches:
    all:
      - query:
          parameter: my_parameter
          exact:
            - required_value
      - query:
          parameter: other_parameter
          ignore_case: true
          begins_with:
             - foo
             - bar
```

### 1.3  Negative matching

Match any paths that are NOT the paths `/public/` or `/html/public/`:

```
  matches:
    all:
      - paths:
          not: True
          begins_with:
            - '/public/'
            - '/html/public/'
```

Match any path that does not END with `/public/`:
```
  matches:
    all:
      - paths:
          not: True
          ends_with:
            - '/public/'
```

### 1.4  Combining different matching methods

Match paths that begin with either `/secret/` or `/topsecret/` EXCEPT the subdirectories `public`:

```
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
```
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
### 1.5 `domain_default` matching

The `matches` directive can only be present in a rule that does *NOT* have the `domain_default` property set, for obvious reasons. A rule that has `domain_default: True` will match any requests to that domain that are not matched by a rule for the same domain that does explicit matching.

Complete rule example:

```
- description: www.domain.local - domain default
  domains:
    - www.mydomain.com
  domain_default: True
  actions:
    backend:
      origin: 'https://default-origin.localdomain'
    header_southbound:
      - set:
        field: 'Host'
        value: 'default-origin.localdomain'
      - set:
        field: 'X-Forwarded-Host'
        value: 'www.mydomain.com'
```

## 2. Actions

### 2.1. Routing

#### 2.1.1 Routing to a single backend

Routes all matched requests to the backend at `https://my-backend.mydomain.com`:

```
  actions:
    backend:
      origin: 'https://my-backend.mydomain.com'
```

#### 2.1.2 Balancing over multiple backends

Spreads the matched requests over two servers:

```
  actions:
    backend:
      servers:
        - 'https://backend-1.mydomain.com'
        - 'https://backend-2.mydomain.com'
```

#### 2.1.3 Multiple backends with custom queue size and connection limits:

```
  actions:
    backend:
      servers:
        - server: 'https://small-backend.mydomain.com'
          max_connections: 32
          max_queued_connections: 16
        - server: 'https://large-backend.mydomain.com'
          max_connections: 2048
          max_queued_connections: 1024
```

### 2.2. Rewriting

#### 2.2.1 Rewriting paths

Add a prefix to the request path:

```
  actions:
    req_path:
      - prefix:
          add: /myprefix
```

Replace a specific part of a path regardless of case:

```
  actions:
    req_path:
      - replace:
          from_exact: '/path/to/replace'
          ignore_case: true
          to: '/new/path'
```

Rewrite a path based on regular expression matching:

```
  actions:
    req_path:
      - replace:
          from_regex: '/some/path/(.*)'
          to_regsub: '/\1'
```

The above actually removes a the prefix '/some/path' from the path, which can also be achieved using the `prefix` structure:

```
  actions:
    req_path:
      - prefix:
          remove: /some/path
```

#### 2.2.2 Rewriting headers

When manipulating headers, _southbound_ is the direction of the incoming request, i.e. toward the origin, and _northbound_ is the direction of the response, i.e. toward the client.

Setting the southbound host header:

```
  actions:
    header_southbound:
      - set:
          field: 'Host'
          value: 'backend-host-name.localdomain'
```

Adding a southbound header that the backend application requires:

```
  actions:
    header_southbound:
      - add:
          field: 'Authorization'
          value: 'My-secret-authorization-token'
```

Setting various northbound headers for access control:

```
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

```
  actions:
    header_northbound:
      - remove: 'X-Robots-Tag'
```

### 2.3. Redirecting

#### 2.3.1 Simple redirection

Temporary (HTTP 307) redirect of all matching requests to a new domain:

```
  actions:
	  redirect:
		  type: temporary
			domain: www.redirectdomain.com
```

Permament (HTTP 308) redirect of the same type, but redirect to HTTP specifically:

```
  actions:
	  redirect:
		  type: permament
			scheme: http
			domain: www.redirectdomain.com
```

Temporary (HTTP 307) redirect of all matching requests to a specific url:

```
  actions:
	  redirect:
		  type: temporary
			url: https://www.redirectdomain.com/redirected/
```

#### 2.3.2 Redirection with rewriting

Temporarily redirect matching requests to a new domain using HTTPS and adjust the path:

```
  actions:
	  redirect:
		  type: temporary
			scheme: https
			domain: www.redirectdomain.com
	    path:
			  - prefix:
					  add: /redirected
```

## 3. Complete examples

### 3.1 Routing requests to a single backend and rewriting request headers

```
rules:
  - description: My production web site
    domains:
      - www.mydomain.com
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
        origin: https://my.origin.com
      header_southbound:
        - set:
            field: 'Host'
            value: 'my.origin.com'
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

```
rules:
  - description: Domain default rule that redirects requests that do not match any other rule
		domains:
		  - www.mydomain.com
    domain_default: True
		actions:
		  redirect:
			  type: permanent
				url: https://my.redirect.url

  - description: Rule to route requests to a certain path to a backend
    domains:
      - www.mydomain.com
    matches:
      all:
        - paths:
            begins_with:
              - '/non-redirecting-path'
    actions:
      backend:
        origin: https://my.origin.com
      header_southbound:
        - set:
            field: 'Host'
            value: 'my.origin.com'
```

### 3.3 Routing requests to different backends based on query parameters

```
rules:
  - description: Rule to route requests with a specific query parameter to a separate backend
    domains:
      - www.mydomain.com
    matches:
      all:
			  - query:
            parameter: special
            exact:
              - True
    actions:
      backend:
        origin: https://special.origin.com
      header_southbound:
        - set:
            field: 'Host'
            value: 'special.origin.com'

	- description: Rule to route requests without a specific query parameter to another backend
    domains:
      - www.mydomain.com
    matches:
      all:
			  - query:
            parameter: special
            exist: False
    actions:
      backend:
        origin: https://other.origin.com
      header_southbound:
        - set:
            field: 'Host'
            value: 'other.origin.com'
```

### 3.4 Redirecting requests to a single URL

```
rules:
  - description: Redirect www.mydomain.com to www.redirect-domain.com using https
    domains:
      - www.mydomain.com
    domain_default: True
    actions:
      redirect:
        type: temporary
        scheme: https
        domain: www.redirect-domain.com
```

### 3.5 Redirecting requests and rewriting the request path

```
rules:
  - description: Redirect mydomain.com/<path> to www.redirect-domain.com/newlocation/<path>
    domains:
      - mydomain.com
      - www.mydomain.com
    domain_default: True
    actions:
      redirect:
        type: temporary
        scheme: https
        domain: www.redirect-domain.com
        path:
          - prefix:
              add: /newlocation
```
