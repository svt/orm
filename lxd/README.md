# Origin Routing Machine deployment

This folder contains tools to build a minimalistic deployment of the Origin Routing Machine. Ansible is used to provision a deployment into an LXD image. See the `Makefile` for the build process. See the `ansible` folder, and specifically `orm_provision.yml` for provisioning details.

## Building

`make build`

## Using

Before sending requests to the container, the configuration for Varnish and HAProxy must be updated. When updated, you can perform manual requests using `curl` or similar tools against the `orm` container IP. You can use both `HTTP` and `HTTPS` on the standard ports, but by default a self-signed certificate is used for `HTTPS` so you need to disable certificate verification (using curl: `curl -k ...`).

There are two convenience scripts:

### `update-orm-config.sh`

Updates the configuration in the `orm` lxd container.

Usage: `update-orm-config.sh config_dir`

Where `config_dir` is a directory containing configuration output by ORM, containing `haproxy.cfg` and `varnish.vcl`.

### `test-orm-config.sh`

Uses `tests` in ORM rule files to test functionality against the `orm` lxd container. For example `./out`.

Usage: `test-orm-config.sh rules_glob`

Where `rules_glob` is a glob for ORM rules to test. For example `orm-rules-test/namespaces/**/*.yml`.

## Requirements

- lxd
- python
- virtualenv
