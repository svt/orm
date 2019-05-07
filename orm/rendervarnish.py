import re

from orm.render import RenderOutput, ORMInternalRenderException
import orm.parser as parser


def vcl_escape_string_to_regex(string):
    regex = re.escape(string)
    regex = vcl_escape_regex(regex)
    return regex


def vcl_escape_regex(regex):
    regex = regex.replace(r"\"", r"\x22")
    regex = regex.replace(r'"', r"\x22")
    # For readability. '/' does not need to be escaped in Varnish regex.
    regex = regex.replace(r"\/", r"/")
    return regex


def vcl_safe_string(string):
    string = string.replace("\n", "")
    split = string.split(r'"}')
    if len(split) == 1:
        if r'"' in split[0]:
            return '{"' + string + '"}'
        return '"' + string + '"'
    return '{"' + r'""} "}" {"'.join(split) + '"}'


def vcl_regex_add_opts(regex, ignore_case):
    reg_options = "(?i)" if ignore_case else ""
    return reg_options + regex


def make_vcl_set_match_variable(rule_id):
    return "variable.set(" + vcl_safe_string("match_" + rule_id) + ", 1);"


def make_vcl_match_variable_defined(rule_id):
    return "variable.defined(" + vcl_safe_string("match_" + rule_id) + ")"


def make_vcl_query_regex(inp, match_function, ignore_case):
    reg_query_beg = "(^|&)"
    reg_query_param_end = "(=|&|$)"
    reg_query_end = "(&|$)"
    reg_query_wc = r"[^&]*"
    regex = None
    esc_param = vcl_escape_string_to_regex(inp["parameter"])
    if match_function == "exist":
        regex = reg_query_beg + esc_param + reg_query_param_end
    else:
        value = inp["value"]
        if match_function == "regex":
            regex = (
                reg_query_beg
                + esc_param
                + "="
                + vcl_escape_regex(value)
                + reg_query_end
            )
        else:
            esc_value = vcl_escape_string_to_regex(value)
            if match_function == "exact":
                regex = reg_query_beg + esc_param + "=" + esc_value + reg_query_end
            elif match_function == "begins_with":
                regex = (
                    reg_query_beg
                    + esc_param
                    + "="
                    + esc_value
                    + reg_query_wc
                    + reg_query_end
                )
            elif match_function == "ends_with":
                regex = (
                    reg_query_beg
                    + esc_param
                    + "="
                    + reg_query_wc
                    + esc_value
                    + reg_query_end
                )
            elif match_function == "contains":
                regex = (
                    reg_query_beg
                    + esc_param
                    + "="
                    + reg_query_wc
                    + esc_value
                    + reg_query_wc
                    + reg_query_end
                )
    if regex is None:
        raise ORMInternalRenderException(
            "ERROR: unhandled query match "
            "function: " + match_function + ":" + str(inp)
        )
    return vcl_regex_add_opts(regex, ignore_case)


def make_vcl_path_regex(value, match_function, ignore_case):
    regex = None
    if match_function == "regex":
        regex = "^{}$".format(vcl_escape_regex(value))
    else:
        escaped_value = vcl_escape_string_to_regex(value)
        if match_function == "exact":
            regex = "^{}$".format(escaped_value)
        elif match_function == "begins_with":
            regex = "^{}.*$".format(escaped_value)
        elif match_function == "ends_with":
            regex = "^.*{}$".format(escaped_value)
        elif match_function == "contains":
            regex = "^.*{}.*$".format(escaped_value)
    if regex is None:
        raise ORMInternalRenderException(
            "ERROR: unhandled path match "
            "function: " + match_function + ":" + str(value)
        )
    return vcl_regex_add_opts(regex, ignore_case)


def indent(indent_depth):
    return "  " * indent_depth


def make_sb_header_action(config_in, config_out, rule_id, indent_depth=0):
    return make_header_action(
        config_in, config_out, rule_id, southbound=True, indent_depth=indent_depth
    )


def make_nb_header_action(config_in, config_out, rule_id, indent_depth=0):
    return make_header_action(
        config_in, config_out, rule_id, southbound=False, indent_depth=indent_depth
    )


def make_header_action(config_in, config_out, rule_id, indent_depth=0, southbound=True):
    # pylint:disable=unused-argument
    hdr_var = "req" if southbound else "resp"
    actions = []
    for header_action in config_in:
        # field name is validated by schema in validator. I guess any
        # valid field name is valid to use in Varnish VCL as well.
        if "remove" in header_action:
            field = header_action["remove"]
            actions.append(
                indent(indent_depth) + "unset " + hdr_var + ".http." + field + ";"
            )
        elif "set" in header_action:
            field = header_action["set"]["field"]
            value = header_action["set"]["value"]
            actions.append(
                indent(indent_depth)
                + "set "
                + hdr_var
                + ".http."
                + field
                + " = "
                + vcl_safe_string(value)
                + ";"
            )
        elif "add" in header_action:
            field = header_action["add"]["field"]
            value = header_action["add"]["value"]
            actions.append(
                indent(indent_depth) + "if (" + hdr_var + ".http." + field + ") {"
            )
            actions.append(
                indent(indent_depth + 1)
                + "set "
                + hdr_var
                + ".http."
                + field
                + " = "
                + hdr_var
                + ".http."
                + field
                + ' + ",";'
            )
            actions.append(indent(indent_depth) + "}")
            actions.append(
                indent(indent_depth)
                + "set "
                + hdr_var
                + ".http."
                + field
                + " = "
                + hdr_var
                + ".http."
                + field
                + " + "
                + vcl_safe_string(value)
                + ";"
            )
        else:
            raise ORMInternalRenderException(
                "ERROR: unhandled header " "action type: " + str(header_action.keys())
            )
    config_out_key = "sb" if southbound else "nb"
    config_out[config_out_key] = actions
    return config_out


def make_redirect_action(config_in, config_out, rule_id, indent_depth=0):
    # pylint:disable=unused-argument
    code = "307"
    if config_in["type"] == "permanent":
        code = "308"
    elif config_in["type"] == "permanent_allow_method_change":
        code = "301"
    elif config_in["type"] == "temporary_allow_method_change":
        code = "302"
    url = config_in.get("url", None)
    if url:
        config_out["sb"] = [
            indent(indent_depth)
            + "return (synth("
            + code
            + ", "
            + vcl_safe_string(url)
            + "));"
        ]
        return config_out
    scheme = config_in.get("scheme", None)
    if scheme:
        config_out["sb"].append(
            indent(indent_depth)
            + 'variable.set("scheme", '
            + vcl_safe_string(scheme)
            + ");"
        )
    else:
        config_out["sb"] += [
            indent(indent_depth) + "if (std.port(server.ip) == 443) {",
            (indent(indent_depth + 1) + 'variable.set("scheme", "https");'),
            indent(indent_depth) + "} else {",
            (indent(indent_depth + 1) + 'variable.set("scheme", "http");'),
            indent(indent_depth) + "}",
        ]
    domain = config_in.get("domain", None)
    if domain:
        config_out["sb"].append(
            indent(indent_depth)
            + 'variable.set("domain", '
            + vcl_safe_string(domain)
            + ");"
        )
    else:
        config_out["sb"].append(
            indent(indent_depth) + 'variable.set("domain", req.http.host);'
        )
    path = config_in.get("path", None)
    if path:
        make_path_mod_actions(path, config_out, rule_id, indent_depth=indent_depth)
    config_out["sb"] += [
        indent(indent_depth) + "call reconstruct_requrl;",
        indent(indent_depth)
        + "return (synth("
        + code
        + ", "
        + 'variable.get("scheme") + "://" + variable.get("domain") + req.url));',
    ]
    return config_out


def make_synth_resp_action(config_in, config_out, rule_id, indent_depth=0):
    synth = indent(3) + "synthetic(" + vcl_safe_string(config_in) + ");"
    synth_clause = make_action_if_clause([synth], rule_id, indent_depth=2)
    config_out["synth"] = synth_clause
    config_out["sb"] = [indent(indent_depth) + 'return (synth(750, ""));']
    return config_out


def make_action_if_clause(actions, rule_id, indent_depth=0):
    if_clause = []
    if_clause.append(
        indent(indent_depth) + "if (" + make_vcl_match_variable_defined(rule_id) + ") {"
    )
    if_clause += actions
    if_clause.append(indent(indent_depth) + "}")
    return if_clause


def make_backend_action(config_in, config_out, rule_id, indent_depth=0):
    # pylint:disable=unused-argument
    # All backend and loadbalancer logic is done by HAProxy.
    # Varnish only sets the ORM ID header and forwards to HAProxy.
    # See renderhaproxy.py
    config_out["sb"] = [
        indent(indent_depth)
        + "set req.http.X-ORM-ID = "
        + vcl_safe_string(rule_id)
        + ";",
        indent(indent_depth) + "set req.backend_hint = round_robin_director.backend();",
        indent(indent_depth) + "call use_backend;",
    ]
    return config_out


def make_trailing_slash_action(config_in, config_out, rule_id, indent_depth=0):
    # pylint:disable=unused-argument
    regex = ""
    action = []
    reg_path_without_trailing = "(?:/[^/?#]+)*"
    reg_post_path = "[#?].*"
    if config_in == "add":
        # Will match all paths without trailing slash,
        # when the last part begins with a period or contains no periods.
        reg_path_end = r"/(?:\.?[^/?#.]+)"
        regex = (
            "^(" + reg_path_without_trailing + reg_path_end + ")"
            "(" + reg_post_path + ")?$"
        )
        sub = r"\1/\2"
    elif config_in == "remove":
        # Will match all paths with a trailing slash.
        regex = "^(" + reg_path_without_trailing + ")/" "(" + reg_post_path + ")?$"
        sub = r"\1\2"
    elif config_in == "do_nothing":
        return config_out
    else:
        raise ORMInternalRenderException(
            "ERROR: unhandled " + "trailing slash action: " + config_in
        )
    action.append(indent(indent_depth) + 'if (req.url ~ "' + regex + '") {')
    action.append(
        indent(indent_depth + 1) + "return (synth(307, "
        'regsub(req.url, "' + regex + '", "' + sub + '")));'
    )
    action.append(indent(indent_depth) + "}")
    config_out["sb"] = action
    return config_out


def make_https_redir_action(config_in, config_out, rule_id, indent_depth=0):
    # pylint:disable=unused-argument
    if not config_in:
        return config_out
    config_out["sb"] = [
        indent(indent_depth) + "if (std.port(server.ip) != 443) {",
        (
            indent(indent_depth + 1)
            + 'return (synth(307, "https://" + req.http.host + req.url));'
        ),
        indent(indent_depth) + "}",
    ]
    return config_out


def make_path_mod_actions(config_in, config_out, rule_id, indent_depth=0):
    # pylint:disable=unused-argument
    actions = []
    for action in config_in:
        if "replace" in action:
            conf = action["replace"]
            actions += make_path_replace_action(conf, indent_depth=indent_depth)
        elif "prefix" in action:
            conf = action["prefix"]
            actions += make_path_prefix_action(conf, indent_depth=indent_depth)
        else:
            raise ORMInternalRenderException(
                "ERROR: unhandled path_mod " "action type: " + action
            )
    config_out["sb"] += actions
    return config_out


def make_path_prefix_action(prefix_config, indent_depth=0):
    config = []
    ignore_case = prefix_config.get("ignore_case", False)
    if "remove" in prefix_config:
        vcl_regex = "^" + vcl_escape_string_to_regex(prefix_config["remove"])
        vcl_regex = vcl_regex_add_opts(vcl_regex, ignore_case)
        config.append(
            indent(indent_depth) + 'variable.set("path", '
            'regsub(variable.get("path"), {}, ""));'.format(vcl_safe_string(vcl_regex))
        )
    if "add" in prefix_config:
        config.append(
            indent(indent_depth)
            + 'variable.set("path", {} + variable.get("path"));'.format(
                vcl_safe_string(prefix_config["add"])
            )
        )
    return config


def make_path_replace_action(replace_config, indent_depth=0):
    # pylint:disable=unused-argument
    ignore_case = replace_config.get("ignore_case", False)
    vcl_regex = None
    vcl_sub = replace_config.get("to", None)
    if "from_regex" in replace_config:
        vcl_regex = make_vcl_path_regex(
            replace_config["from_regex"], "regex", ignore_case
        )
        vcl_sub = replace_config.get("to_regsub", vcl_sub)
    elif "from_exact" in replace_config:
        vcl_regex = make_vcl_path_regex(
            replace_config["from_exact"], "exact", ignore_case
        )
    if vcl_sub is None or vcl_regex is None:
        raise ORMInternalRenderException(
            "ERROR: could not generate "
            "substitution using replace config "
            "keys: " + str(replace_config.keys())
        )
    return [
        indent(indent_depth) + 'variable.set("path", '
        'regsub(variable.get("path"), {reg}, {sub}));'.format(
            reg=vcl_safe_string(vcl_regex), sub=vcl_safe_string(vcl_sub)
        )
    ]


class RenderVarnish(RenderOutput):
    # pylint:disable=too-many-instance-attributes
    def get_unique_vcl_name(self, namespace, raw_name):
        if not namespace in self.names:
            self.names[namespace] = {}
        name = parser.normalize_lower("_".join((namespace, raw_name)))
        # Varnish doesn't like names longer than 40 characters
        if len(name) > 35:
            name = name[:35]
        if name in self.names[namespace]:
            self.names[namespace][name] += 1
            return "_".join((name, str(self.names[namespace][name])))
        self.names[namespace][name] = 1
        return name

    def make_match_path(self, fun, inp):
        value = inp["value"]
        ignore_case = inp.get("ignore_case", False)
        vcl_regex = make_vcl_path_regex(value, fun, ignore_case)
        return 'variable.get("path") ~ ' + vcl_safe_string(vcl_regex)

    def make_match_query(self, fun, inp):
        ignore_case = inp.get("ignore_case", False)
        vcl_regex = make_vcl_query_regex(inp, fun, ignore_case)
        return 'variable.get("query") ~ ' + vcl_safe_string(vcl_regex)

    def make_match_domain(self, fun, inp):
        if fun == "exact":
            return "req.http.host == " + vcl_safe_string(inp)
        raise ORMInternalRenderException(
            "ERROR: unhandled domain match: " + fun + ":" + str(inp)
        )

    def make_condition_match(self, match):
        src = match["source"]
        fun = match["function"]
        inp = match["input"]
        if src == "path":
            return self.make_match_path(fun, inp)
        if src == "domain":
            return self.make_match_domain(fun, inp)
        if src == "query":
            return self.make_match_query(fun, inp)
        raise ORMInternalRenderException(
            "ERROR: unhandled match source: " + src + ":" + fun + ":" + str(inp)
        )

    def handle_condition_list(
        self, operator, match_tree_list, negate=False, indent_depth=0
    ):
        first = True
        expr = "!" if negate else " "
        if len(match_tree_list) == 1:
            return expr + self.parse_match_tree(match_tree_list[0], indent_depth)
        for match_tree in match_tree_list:
            if first:
                expr += "(" + " " * 2
                first = False
            else:
                expr += "\n" + indent(indent_depth) + "   " + operator + " "
            expr += self.parse_match_tree(match_tree, indent_depth + 2)
        expr += ")"
        return expr

    def parse_match_tree(self, match_tree, indent_depth=0, negate=False):
        if "and" in match_tree:
            return self.handle_condition_list(
                "&&", match_tree["and"], negate=negate, indent_depth=indent_depth
            )
        if "or" in match_tree:
            return self.handle_condition_list(
                "||", match_tree["or"], negate=negate, indent_depth=indent_depth
            )
        if "match" in match_tree:
            opt_negate = "!" if negate else ""
            return opt_negate + self.make_condition_match(match_tree["match"])
        if "not" in match_tree:
            return self.parse_match_tree(
                match_tree["not"], indent_depth=indent_depth, negate=True
            )
        raise ORMInternalRenderException(
            "ERROR: unhandled condition operator: " + str(match_tree.keys)
        )

    def make_condition(self, match_tree, rule_id, indent_depth=0):
        condition = []
        expr = self.parse_match_tree(match_tree, indent_depth=indent_depth + 1)
        if_clause = indent(indent_depth) + "if (" + expr + ")"
        condition += if_clause.split("\n")
        condition.append(indent(indent_depth) + "{")
        condition.append(
            indent(indent_depth + 1) + make_vcl_set_match_variable(rule_id)
        )
        condition.append(indent(indent_depth) + "}")
        return condition

    def make_match_sub(self, match_tree, rule_id, match_sub_name):
        indent_depth = 0
        sub = []
        sub.append("sub " + match_sub_name + " {")
        sub += self.make_condition(match_tree, rule_id, indent_depth=indent_depth + 1)
        sub.append("}")
        return sub

    def make_actions(
        self,
        action_config,
        rule_id,
        domain=None,
        match_sub_name=None,
        indent_depth=0,
        is_global=False,
    ):
        # pylint:disable=too-many-locals,too-many-arguments,too-many-branches
        # pylint:disable=too-many-statements
        if not domain and not is_global:
            raise ORMInternalRenderException(
                "ERROR: One of domain and " + "is_global must be set!"
            )
        # Order is important
        supported_actions = [
            {
                "name": "https_redirection",
                "func": make_https_redir_action,
            },  # Must be first
            {
                "name": "trailing_slash",
                "func": make_trailing_slash_action,
            },  # Must be second
            {"name": "synthetic_response", "func": make_synth_resp_action},
            {"name": "redirect", "func": make_redirect_action},
            {"name": "header_southbound", "func": make_sb_header_action},
            {"name": "req_path", "func": make_path_mod_actions},
            {"name": "backend", "func": make_backend_action},
            {"name": "header_northbound", "func": make_nb_header_action},
        ]
        for action_name in action_config:
            present = False
            for supported_action in supported_actions:
                if action_name == supported_action["name"]:
                    present = True
            if not present:
                raise ORMInternalRenderException(
                    "ERROR: unhandled " + "action type: " + action_name
                )
        if "backend" in action_config:
            self.uses_sub_use_backend = True
        if "redirect" in action_config and "url" not in action_config:
            self.uses_sub_reconstruct_requrl = True
        sb = []
        nb = []
        for action in supported_actions:
            action_name = action["name"]
            action_function = action["func"]
            if action_name not in action_config:
                continue
            config_out = {"sb": [], "nb": [], "synth": []}
            action_function(
                config_in=action_config[action_name],
                config_out=config_out,
                rule_id=rule_id,
                indent_depth=indent_depth + 1,
            )
            sb += config_out["sb"]
            nb += config_out["nb"]
            self.synthetic_responses += config_out["synth"]
        if is_global:
            if sb:
                self.global_actions_southbound += sb
            if nb:
                self.global_actions_northbound += nb
        else:
            if sb:
                sb.insert(
                    0, indent(indent_depth + 1) + "call global_actions_southbound;"
                )
                if match_sub_name:
                    actions = []
                    actions.append(
                        (indent(indent_depth) + "call " + match_sub_name + ";")
                    )
                    actions += make_action_if_clause(
                        sb, rule_id, indent_depth=indent_depth
                    )
                    self.actions_southbound.setdefault(domain, [])
                    self.actions_southbound[domain] += actions
                else:  # If there is no match_sub_name, it is a default rule
                    actions = []
                    # Set variable when default actions are reached in
                    # vcl_recv (southbound) so we know whether to perform
                    # the default northbound actions
                    actions.append(
                        indent(indent_depth + 1) + make_vcl_set_match_variable(rule_id)
                    )
                    actions += sb
                    self.default_actions_southbound.setdefault(domain, [])
                    self.default_actions_southbound[domain] += actions
            if nb:
                if match_sub_name:
                    actions = make_action_if_clause(
                        nb, rule_id, indent_depth=indent_depth
                    )
                    self.actions_northbound.setdefault(domain, [])
                    self.actions_northbound[domain] += actions
                else:  # If there is no match_sub_name, it is a default rule
                    # Only perform default northbound actions if variable is set
                    # (that is, only when the default southbound actions did)
                    actions = make_action_if_clause(
                        nb, rule_id, indent_depth=indent_depth
                    )
                    self.default_actions_northbound.setdefault(domain, [])
                    self.default_actions_northbound[domain] += actions
        # Return True if we generated an action
        return config_out["sb"] or config_out["nb"] or config_out["synth"]

    def make_southbound_actions(self, domains):
        config = []
        for domain in domains:
            actions = self.actions_southbound[domain]
            default_actions = self.default_actions_southbound[domain]
            if not actions and not default_actions:
                continue
            config.append(
                indent(1) + "if (req.http.host == " + vcl_safe_string(domain) + ") {"
            )
            for line in actions:
                config.append(indent(1) + line)
            if default_actions:
                config.append(
                    indent(2) + "# ORM: Default southbound actions for " + domain
                )
                for line in default_actions:
                    config.append(indent(1) + line)
            config.append(indent(1) + "}")
        return config

    def make_northbound_actions(self, domains):
        config = []
        for domain in domains:
            actions = self.actions_northbound[domain]
            default_actions = self.default_actions_northbound[domain]
            if not actions and not default_actions:
                continue
            config += actions
            if default_actions:
                config.append(
                    indent(1) + "# ORM: Default northbound actions for " + domain
                )
                config += default_actions
        return config

    def __init__(self, rule_docs, globals_doc=None):
        # pylint:disable=too-many-locals,too-many-statements
        super().__init__(
            rule_docs=rule_docs, globals_doc=globals_doc, output_file="varnish.vcl"
        )
        self.names = {}
        self.matches = []
        self.actions_southbound = {}
        self.actions_northbound = {}
        self.default_actions_southbound = {}
        self.default_actions_northbound = {}
        self.global_actions_southbound = []
        self.global_actions_northbound = []
        self.synthetic_responses = []
        self.uses_sub_use_backend = False
        self.uses_sub_reconstruct_requrl = False
        self.directors = {}
        for domain, rules in rule_docs.items():
            self.actions_southbound.setdefault(domain, [])
            self.actions_northbound.setdefault(domain, [])
            self.default_actions_southbound.setdefault(domain, [])
            self.default_actions_northbound.setdefault(domain, [])
            for rule in rules:
                description = rule.get("description")
                orm_file = rule.get("_orm_source_file").split("/", 1)[1:][0]
                rule_id = rule.get("_rule_id")
                config_debug_line = "\n# " + orm_file + " - " + description
                if rule.get("domain_default", False):
                    # Create default southbound and northbound actions
                    actions = rule.get("actions")
                    self.make_actions(actions, rule_id, domain=domain, indent_depth=1)
                else:
                    # Create a Varnish subroutine (sub) to match current rule
                    matches = rule.get("matches")
                    match_tree = parser.get_match_tree(matches)
                    self.matches.append(config_debug_line)
                    match_sub_name = self.get_unique_vcl_name("match", rule_id)
                    match_sub = self.make_match_sub(match_tree, rule_id, match_sub_name)
                    # Create regular southbound and northbound actions
                    # (using the matching sub).
                    actions = rule.get("actions")
                    if self.make_actions(
                        actions,
                        rule_id,
                        domain=domain,
                        match_sub_name=match_sub_name,
                        indent_depth=1,
                    ):
                        self.matches += match_sub

        # Create global southbound and northbound actions
        global_actions = self.globals_doc.get("global_actions", None)
        if global_actions:
            rule_id = "global"
            self.make_actions(global_actions, rule_id, indent_depth=0, is_global=True)

        if self.uses_sub_use_backend:
            self.uses_sub_reconstruct_requrl = True
        southbound_config = self.make_southbound_actions(rule_docs.keys())
        northbound_config = self.make_northbound_actions(rule_docs.keys())
        haproxy = self.globals_doc.get("haproxy", {})
        self.config = self.jinja.get_template("varnish.vcl.j2").render(
            global_actions_southbound=self.global_actions_southbound,
            global_actions_northbound=self.global_actions_northbound,
            matches=self.matches,
            synthetic_responses=self.synthetic_responses,
            uses_sub_use_backend=self.uses_sub_use_backend,
            uses_sub_reconstruct_requrl=self.uses_sub_reconstruct_requrl,
            southbound_actions=southbound_config,
            northbound_actions=northbound_config,
            haproxy_address=haproxy.get("address", "localhost"),
        )
