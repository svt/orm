# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2019-08-27

- Fix log format for external ORM listener
- Extended documentation (rule examples)

## [1.1.1] - 2019-05-28

### Changed
- Extended log format to include multiple timing fields.

## [1.1.0] - 2019-05-09

### Added
- Add support for `max_connections` + `max_queued_connections` to `servers` in [backend](https://github.com/SVT/orm/blob/1.1.0/docs/syntax_reference.md#backend)
- Explicitly set timeout queue 10s in haproxy template.
- Travis CI

### Changed
- Port echo_server.py used in deployment tests to python3.

## [1.0.0] - 2019-03-15

Open source release.
