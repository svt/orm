import os
from sys import stderr
import shutil
import re
import string
import concurrent.futures
import time
import json
import pickle

import pkg_resources
from rfc3986 import validators, uri_reference
from rfc3986.exceptions import RFC3986Exception
import jsonschema
from jsonschema import Draft4Validator, FormatChecker
from greenery import lego

import orm.parser as parser


class ORMSchemaException(Exception):
    pass


class ValidateRuleConstraintsException(Exception):
    pass


def validate_rule_files(yml_files, cache_path=None):
    valid = True
    for yml_file in yml_files:
        if not validate_rule_schema(yml_file):
            valid = False
    if not valid:
        return False
    return validate_rule_constraints(yml_files, cache_path=cache_path)


def validate_globals_file(globals_file):
    return validate_globals_schema(globals_file)


orm_schemas = {"rules": {}, "globals": {}}

orm_schemas["rules"]["1"] = "rules-1.json"
orm_schemas["globals"]["1"] = "globals-1.json"


def get_schema(yml_file, yml_doc, schema_type="rules"):
    schema_version = str(yml_doc.get("schema_version", None))
    if not schema_version:
        raise ORMSchemaException("ORM doc missing schema_version (" + yml_file + ")")
    schema_file = orm_schemas[schema_type].get(schema_version, None)
    if not schema_file:
        raise ORMSchemaException(
            "ORM doc using unknown schema_version. "
            "Found '" + schema_version + "'. "
            "Supports " + str(list(orm_schemas.keys())) + " (" + yml_file + ")"
        )
    json_file = open(os.path.join(schema_dir, schema_file))
    schema = json.load(json_file)
    json_file.close()
    return schema


noncontrol_US_ASCII = r"\u0020-\u007E"
noncontrol_unicode = r"\u0020-\u007E\u00A0-\uFFFF"

rfc7230_token = r"0-9a-zA-Z!#$%&\'*+\-.^_`|~"
rfc7230_vchar = noncontrol_US_ASCII

rfc7230_header_field_name = r"^[" + rfc7230_token + "]+$"
regex_http_header_field_name = re.compile(rfc7230_header_field_name)


@FormatChecker.cls_checks("http-header-field-name")
def format_check_http_header_field_name(instance):
    return bool(regex_http_header_field_name.search(instance))


# Do not allow rfc7230 obs-text and obs-fold in field-value for now.
# Wait and see if someone complains...
rfc7230_header_field_value = r"^[" + rfc7230_vchar + "\t]*$"
regex_http_header_field_value = re.compile(rfc7230_header_field_value)


@FormatChecker.cls_checks("http-header-field-value")
def format_check_http_header_field_value(instance):
    return bool(regex_http_header_field_value.search(instance))


uri_all_components_validator = (
    validators.Validator()
    .require_presence_of("scheme", "host", "path", "query", "fragment")
    .check_validity_of("scheme", "host", "path", "query", "fragment")
)


@FormatChecker.cls_checks("uri-path")
def format_check_uri_path(instance):
    uri = uri_reference("http://example.com/{}?param=value#fragment".format(instance))
    try:
        uri_all_components_validator.validate(uri)
    except RFC3986Exception:
        return False
    return (
        uri.scheme == "http"
        and uri.authority == "example.com"
        and uri.path == "/" + instance
        and uri.query == "param=value"
        and uri.fragment == "fragment"
    )


@FormatChecker.cls_checks("uri-query")
def format_check_uri_query_value(instance):
    uri = uri_reference("http://example.com/path?{}#fragment".format(instance))
    try:
        uri_all_components_validator.validate(uri)
    except RFC3986Exception:
        return False
    return (
        uri.scheme == "http"
        and uri.authority == "example.com"
        and uri.path == "/path"
        and uri.query == instance
        and uri.fragment == "fragment"
    )


uri_validator = validators.Validator()


@FormatChecker.cls_checks("uri")
def format_check_url(instance):
    uri = uri_reference(instance)
    try:
        uri_validator.validate(uri)
    except RFC3986Exception:
        return False
    return True


def format_check_ip(instance):
    if not instance:
        return False
    for part in instance.split("."):
        if int(part) < 0 or int(part) > 255:
            return False
    return True


def format_check_netmask(instance):
    return instance and int(instance) > 0 and int(instance) <= 32


reg_integer = "(0|[1-9][0-9]*)"

reg_ipv4 = "(" + reg_integer + r"\.){3}" + reg_integer
ipv4_netmask_delim = "/"
reg_ipv4_network = reg_ipv4 + ipv4_netmask_delim + reg_integer

regex_network = re.compile("^" + reg_ipv4_network + "$")


@FormatChecker.cls_checks("network")
def format_check_network(instance):
    if not bool(regex_network.search(instance)):
        return False
    ip, mask = instance.split(ipv4_netmask_delim)
    if not format_check_ip(ip) or not format_check_netmask(mask):
        return False
    return True


regex_unix_user_or_group = re.compile(r"^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$")


@FormatChecker.cls_checks("unix_user_or_group")
def format_unix_user_or_group(instance):
    return bool(regex_unix_user_or_group.search(instance))


rfc2396_scheme = r"[a-zA-Z][-+.a-zA-Z0-9]*"
rfc1123_hostname = (
    r"(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*"
    r"([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])"
)
reg_port = r"[1-9][0-9]*"


def format_check_hostname(instance):
    return instance and len(instance) > 0 and len(instance) <= 255


def format_check_port(instance):
    return instance and int(instance) > 0 and int(instance) <= 65535


regex_hostport = re.compile(
    "^" + rfc1123_hostname + "(" + parser.port_delim + reg_port + ")?$"
)


@FormatChecker.cls_checks("hostname_with_port")
def format_check_hostname_with_port(instance):
    if not bool(regex_hostport.search(instance)):
        return False
    host, port = (None, None)
    if parser.port_delim in instance:
        host, port = instance.split(parser.port_delim)
    else:
        host = instance
    if not format_check_hostname(host):
        return False
    if port and not format_check_port(port):
        return False
    return True


orm_origin = (
    r"^("
    + rfc2396_scheme
    + parser.scheme_delim
    + ")?"
    + rfc1123_hostname
    + r"("
    + parser.port_delim
    + reg_port
    + ")?$"
)
regex_origin = re.compile(orm_origin)


@FormatChecker.cls_checks("origin")
def format_check_origin(instance):
    if not isinstance(instance, str):
        return False
    if not bool(regex_origin.search(instance)):
        return False
    scheme, host, port = (None, None, None)
    hostport = instance
    if parser.scheme_delim in instance:
        scheme, hostport = instance.split(parser.scheme_delim)
        if scheme not in ["http", "https"]:
            return False
    if parser.port_delim in hostport:
        host, port = hostport.split(parser.port_delim)
        if not format_check_port(port):
            return False
    else:
        host = hostport
    if not format_check_hostname(host):
        return False
    return True


@FormatChecker.cls_checks("orm_regex")
def format_check_orm_regex(instance):
    # pylint:disable=broad-except
    try:
        lego.parse(instance)
    except Exception:
        return False
    return True


regex_orm_regsub = re.compile("^[" + noncontrol_unicode + "]*$")


@FormatChecker.cls_checks("orm_regsub")
def format_check_orm_regsub(instance):
    return bool(regex_orm_regsub.search(instance))


format_checker = FormatChecker()
schema_dir = pkg_resources.resource_filename(__name__, "schemas/")
schema_resolver = jsonschema.RefResolver("file://" + schema_dir, None)


def validate_rule_schema(source_file):
    valid = True
    for doc in parser.parse_yaml_file(source_file):
        schema = get_schema(source_file, doc, schema_type="rules")
        if not validate_schema(source_file, doc, schema):
            valid = False
    return valid


def validate_globals_schema(source_file):
    doc = parser.parse_globals(source_file)
    schema = get_schema(source_file, doc, schema_type="globals")
    return validate_schema(source_file, doc, schema)


def validate_schema(source_file, doc, schema):
    v = Draft4Validator(schema, format_checker=format_checker, resolver=schema_resolver)
    errors = sorted(v.iter_errors(doc), key=str)
    if errors:
        best_error = jsonschema.exceptions.best_match(errors)
        term_cols = shutil.get_terminal_size().columns
        error_msg = (
            "=" * term_cols + "\n"
            "ERROR VALIDATING SCHEMA: " + source_file + "\n" + "=" * term_cols + "\n"
            "PROBABLE ROOT CAUSE:\n" + "-" * term_cols + "\n" + str(best_error) + "\n"
            "OTHER ERRORS:\n" + "-" * term_cols + "\n"
        )
        for error in errors:
            if error != best_error:
                error_msg += str(error) + "\n" + "-" * term_cols
        print(error_msg, file=stderr)
        return False
    return True


def is_ascii_letter_range(start_char, end_char):
    return (
        start_char in string.ascii_letters
        and end_char in string.ascii_letters
        and (
            (
                start_char.isupper()
                and end_char.isupper()
                or (start_char.islower() and end_char.islower())
            )
        )
    )


def lego_ignore_case(instance):
    in_char_class = False
    new_inst = ""
    i = 0
    prev_char = ""
    while i < len(instance):
        char = instance[i]
        if char == "[" and prev_char != "\\":
            in_char_class = True
            new_inst += char
            i += 1
        elif char == "]" and prev_char != "\\":
            in_char_class = False
            new_inst += char
            i += 1
        elif in_char_class:
            if instance[i + 1] == "-" and char != "\\":  # character range
                end_char = instance[i + 2]
                if is_ascii_letter_range(char, end_char):
                    # Only be case insensitive in letter-only ranges
                    # If we need to support other ranges, it is better to
                    # add ignore-case support to greenery.lego
                    new_inst += (
                        char.lower()
                        + "-"
                        + end_char.lower()
                        + char.upper()
                        + "-"
                        + end_char.upper()
                    )
                else:
                    # Do not touch weird ranges
                    new_inst += instance[i : i + 3]
                i += 3
                prev_char = end_char
            elif char.isalpha():
                new_inst += char.lower() + char.upper()
                i += 1
            else:
                new_inst += char
                i += 1
        else:
            if char.isalpha():
                new_inst += "[" + char.lower() + char.upper() + "]"
            else:
                new_inst += char
            i += 1
        prev_char = instance[i - 1]
    return new_inst


def lego_re_escape(instance):
    for special_char in "\\{}[].*+?|":
        instance = instance.replace(special_char, "\\" + special_char)
    return instance


def fsm_parse_regex_task(regex, negate, alphabet):
    fsm = lego.parse(regex).to_fsm(alphabet)
    return fsm.everythingbut() if negate else fsm


def fsm_negate_task(fsm):
    return fsm.everythingbut()


def fsm_action_task(action, fsm1, fsm2):
    if action == "and":
        return fsm1 & fsm2
    elif action == "or":
        return fsm1 | fsm2
    else:
        raise ValidateRuleConstraintsException(
            "Unknown fsm_action_task " "action: " + action
        )


def get_match_path_fsm(match_tree, worker_pool=None):
    if worker_pool is None:
        worker_pool = concurrent.futures.ProcessPoolExecutor(max_workers=1)
    alphabet = set(string.printable)

    def handle_condition_list(data_list_in, op, negate):
        def divide_and_conquer(fsm_list, op):
            num_items = len(fsm_list)
            fsm_future1 = None
            fsm_future2 = None
            if num_items == 1:
                return fsm_list[0]
            elif num_items == 2:
                fsm_future1 = fsm_list[0]
                fsm_future2 = fsm_list[1]
            else:
                half = num_items // 2
                fsm_future1 = divide_and_conquer(fsm_list[:half], op)
                fsm_future2 = divide_and_conquer(fsm_list[half:], op)
            if fsm_future1 is None and fsm_future2 is None:
                return None
            if fsm_future1 is None:
                return fsm_future2
            if fsm_future2 is None:
                return fsm_future1
            fsm_result1 = fsm_future1.result()
            fsm_result2 = fsm_future2.result()
            future = worker_pool.submit(fsm_action_task, op, fsm_result1, fsm_result2)
            return future

        fsm_future = divide_and_conquer(data_list_in, op)
        if fsm_future is not None and negate:
            fsm_result = fsm_future.result()
            fsm_future = worker_pool.submit(fsm_negate_task, fsm_result)
        return fsm_future

    def handle_match(src, fun, inp, negate):
        if not src == "path":
            return None
        value = inp["value"]
        lego_regex = value if fun == "regex" else lego_re_escape(value)
        if inp.get("ignore_case", False):
            lego_regex = lego_ignore_case(lego_regex)
        if fun == "begins_with":
            regex = lego_regex + r".*"
        elif fun == "ends_with":
            regex = r".*" + lego_regex
        elif fun == "contains":
            regex = r".*" + lego_regex + r".*"
        elif fun in ("exact", "regex"):
            regex = lego_regex
        else:
            raise ValidateRuleConstraintsException(
                "Handling of " "match function " + str(fun) + " not implemented."
            )
        future = worker_pool.submit(fsm_parse_regex_task, regex, negate, alphabet)
        return future

    func = {
        "handle_condition_list": handle_condition_list,
        "handle_match": handle_match,
    }
    fsm_future = parser.traverse_match_tree(func, match_tree)
    if fsm_future is None:
        return lego.parse(".*").to_fsm(alphabet)
    fsm_result = fsm_future.result()
    return fsm_result


def fsm_collision(one_fsm, two_fsm):
    return not one_fsm.isdisjoint(two_fsm)


def validate_constraints_domain_default(domain_rules):
    # Assert there is only one domain_default per domain
    print("Checking for domain_default collisions...")
    for domain, rules in domain_rules.items():
        domain_default_rule = None
        for rule in rules:
            domain_default = rule.get("domain_default", None)
            if domain_default is not None:
                if not domain_default:
                    print()
                    print(
                        "ERROR: Using domain_default and setting it to false "
                        " is not allowed"
                    )
                    print(rule["_orm_source_file"] + " (" + rule["description"] + ")")
                    return False
                if domain_default_rule:
                    print()
                    print("ERROR: Multiple domain_default for domain: " + domain)
                    print("Only one domain_default allowed per domain.")
                    print(rule["_orm_source_file"] + " (" + rule["description"] + ")")
                    print("collides with")
                    # pylint:disable=unsubscriptable-object
                    print(
                        domain_default_rule["_orm_source_file"]
                        + " ("
                        + domain_default_rule["description"]
                        + ")"
                    )
                    return False
                domain_default_rule = rule
    return True


def validate_constraints_rule_collision(domain_rules, cache_path=None):
    # pylint:disable=too-many-locals,too-many-branches,too-many-statements
    # Assert all paths are unique (collision check) per domain
    print("Checking for path collisions...")
    fsm_gen_start = time.time()
    cpu_count = os.cpu_count()
    print("Using a pool of {} workers".format(cpu_count))
    worker_pool = concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count)
    admin_pool = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count)
    fsm_futures = {}
    fsm_cache = {}
    fsm_cache_hits = {}
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, "rb") as fsm_cache_file:
            fsm_cache = pickle.load(fsm_cache_file)
    for domain, rules in domain_rules.items():
        for rule in rules:
            # Create an FSM for each rule's match tree paths
            if rule.get("domain_default", False):
                continue
            matches = rule["matches"]
            match_tree = parser.get_match_tree(matches)
            fsm_cache_key = domain + str(match_tree)
            if fsm_cache_key in fsm_cache:
                fsm_cache_hits[fsm_cache_key] = fsm_cache.pop(fsm_cache_key)
                continue
            future = admin_pool.submit(
                get_match_path_fsm, match_tree, worker_pool=worker_pool
            )
            fsm_futures[future] = {
                "desc": rule["description"],
                "file": rule["_orm_source_file"],
                "domain": domain,
                "cache_key": fsm_cache_key,
            }
    # Set the cache to hits only to purge unused entries.
    fsm_cache = fsm_cache_hits
    rule_fsm_list = []
    for fsm_future in concurrent.futures.as_completed(fsm_futures):
        fsm = fsm_future.result()
        fsm_entry = fsm_futures[fsm_future]
        fsm_entry["fsm"] = fsm
        print("Generated FSM for " + fsm_entry["file"] + ": " + fsm_entry["desc"])
        rule_fsm_list.append(fsm_entry)

    print(
        "Got {} FSM:s. {} from cache. {} freshly generated.".format(
            str(len(rule_fsm_list) + len(fsm_cache.keys())),
            str(len(fsm_cache.keys())),
            str(len(rule_fsm_list)),
        )
    )
    print("FSM generation took: {}s".format(str(round(time.time() - fsm_gen_start, 2))))
    collision_check_start = time.time()
    collision_futures = {}
    for i, fsm_one in enumerate(rule_fsm_list):
        # First check the new FSM:s against the other new FSM:s
        j = i + 1
        while j < len(rule_fsm_list):
            fsm_two = rule_fsm_list[j]
            if fsm_one["domain"] == fsm_two["domain"]:
                future = worker_pool.submit(
                    fsm_collision, fsm_one["fsm"], fsm_two["fsm"]
                )
                collision_futures[future] = {"fsm_one": fsm_one, "fsm_two": fsm_two}
            j += 1
        # Then check the new FSM:s against the cached FSM:s
        for cache_key in fsm_cache:
            fsm_two = fsm_cache[cache_key]
            if fsm_one["domain"] == fsm_two["domain"]:
                future = worker_pool.submit(
                    fsm_collision, fsm_one["fsm"], fsm_two["fsm"]
                )
                collision_futures[future] = {"fsm_one": fsm_one, "fsm_two": fsm_two}
    collision_messages = []
    colliding_fsm_cache_keys = []
    for collision_future in concurrent.futures.as_completed(collision_futures):
        if collision_future.result():
            collision_data = collision_futures[collision_future]
            fsm_one = collision_data["fsm_one"]
            fsm_two = collision_data["fsm_two"]
            colliding_fsm_cache_keys += [fsm_one["cache_key"], fsm_two["cache_key"]]
            collision_messages.append(
                "\nFound path collision for domain: {domain}\n"
                "{first_file} ({first_desc})\n"
                "collides with\n"
                "{second_file} ({second_desc})\n".format(
                    domain=fsm_one["domain"],
                    first_file=fsm_one["file"],
                    first_desc=fsm_one["desc"],
                    second_file=fsm_two["file"],
                    second_desc=fsm_two["desc"],
                )
            )
    print(
        "Path collision check took: "
        + str(round(time.time() - collision_check_start, 2))
        + "s"
    )
    if cache_path:
        print("Writing FSM cache to {}".format(cache_path))
        # Add newly generated FSM:s to cache
        for fsm_entry in rule_fsm_list:
            cache_key = fsm_entry["cache_key"]
            # Only add to cache if it did not collide with anything.
            # The cache must only contain FSM:s which does not collide
            # with any other FSM in the cache.
            if cache_key not in colliding_fsm_cache_keys:
                fsm_cache[cache_key] = fsm_entry
        with open(cache_path, "wb") as fsm_cache_file:
            pickle.dump(fsm_cache, fsm_cache_file)
    if collision_messages:
        for msg in collision_messages:
            print(msg)
        return False
    return True


# Validate constraints not covered by schema validation
def validate_rule_constraints(yml_files=None, cache_path=None):
    orm_docs = parser.parse_rules(yml_files)
    print("Validating additional ORM constraints...")
    if not validate_constraints_domain_default(orm_docs["rules"]):
        return False
    if not validate_constraints_rule_collision(
        orm_docs["rules"], cache_path=cache_path
    ):
        return False
    return True
