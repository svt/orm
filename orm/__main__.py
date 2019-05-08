#!/usr/bin/env python3

import argparse

import orm.parser as parser
import orm.validator as validator
from orm.rendervarnish import RenderVarnish
from orm.renderhaproxy import RenderHAProxy
from orm.runtests import run_tests


def main():
    # pylint:disable=too-many-branches,too-many-statements
    """ Main function! """

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-o", "--output-dir", type=str, help="Output file directory."
    )
    arg_parser.add_argument(
        "-r",
        "--orm-rules-path",
        type=str,
        default="namespaces/**/*.yml",
        help="Glob specifying ORM rule files.",
    )
    arg_parser.add_argument(
        "-G",
        "--globals-path",
        type=str,
        default=None,
        help="Path to ORM global settings file.",
    )
    arg_parser.add_argument(
        "--cache-path",
        type=str,
        default=None,
        help="Path to collision check cache file. Caching "
        "is disabled if no path is specified.",
    )
    arg_parser.add_argument(
        "-c",
        "--check",
        help="Only validate rules, no config generated.",
        action="store_true",
        default=False,
    )
    arg_parser.add_argument(
        "-C",
        "--no-check",
        help="Do not validate rules.",
        action="store_true",
        default=False,
    )
    arg_parser.add_argument(
        "-t",
        "--test-target",
        help="Run tests against the provided URL.",
        metavar="URL",
        type=str,
        default=None,
    )
    arg_parser.add_argument(
        "-k",
        "--test-target-insecure",
        help="Do not verify test target certificates.",
        action="store_true",
        default=False,
    )

    args = arg_parser.parse_args()
    yml_files = parser.list_rules_files(args.orm_rules_path)
    if not yml_files:
        print("ERROR: Found no files using glob: {}".format(args.orm_rules_path))
        exit(1)

    if args.globals_path:
        if not validator.validate_globals_file(args.globals_path):
            print("ERROR: Global settings not valid")
            exit(1)

    if args.check and args.no_check:
        print("ERROR: --check together with --no-check does not make sense.")
        exit(1)
    if not args.no_check:
        print("Validating ORM rule files...")
        if not validator.validate_rule_files(
            yml_files=yml_files, cache_path=args.cache_path
        ):
            print("ERROR: Not valid")
            exit(1)
    if args.check:
        print("All checks passed.")
        exit(0)

    parsed_globals = None
    defaults = None
    if args.globals_path:
        parsed_globals = parser.parse_globals(args.globals_path)
        defaults = parsed_globals.get("defaults", None)

    parsed_rules = parser.parse_rules(yml_files=yml_files, defaults=defaults)
    domain_rules = parsed_rules["rules"]
    tests = parsed_rules["tests"]

    if args.test_target:
        print("Run tests against %s" % args.test_target)
        run_tests(
            tests=tests,
            target=args.test_target,
            verify_certs=(not args.test_target_insecure),
        )
        exit(0)

    print("Rendering Varnish config...")
    render_varnish = RenderVarnish(rule_docs=domain_rules, globals_doc=parsed_globals)
    print("Rendering HAProxy config...")
    render_haproxy = RenderHAProxy(rule_docs=domain_rules, globals_doc=parsed_globals)
    if not args.output_dir:
        render_varnish.print_config()
        render_haproxy.print_config()
    else:
        render_varnish.write_config_to_file(args.output_dir)
        render_haproxy.write_config_to_file(args.output_dir)
        print("Config written to " + args.output_dir)


if __name__ == "__main__":
    main()
