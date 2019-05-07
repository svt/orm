from orm.render import RenderOutput, ORMInternalRenderException
import orm.parser as parser


def make_custom_internal_healthcheck(healthcheck_config):
    config = []
    if not healthcheck_config:
        return config
    if "http" in healthcheck_config:
        http_config = healthcheck_config["http"]
        path = http_config["path"]
        method = http_config.get("method", "GET")
        check_option = "option httpchk {} {}".format(method, path)
        domain = http_config.get("domain", None)
        if domain:
            check_option += r" HTTP/1.1\nHost:\ " + domain
        config.append("    " + check_option)
        config.append("    http-check expect ! rstatus ^5")
    else:
        raise ORMInternalRenderException(
            "ERROR: unhandled "
            "custom_internal_healthcheck type: " + healthcheck_config.keys()
        )
    return config


class RenderHAProxy(RenderOutput):
    def make_backend_action(self, backend_config, rule_id):
        origins = []
        if "origin" in backend_config:
            origins.append(backend_config["origin"])
        elif "servers" in backend_config:
            origins += backend_config["servers"]
        else:
            raise ORMInternalRenderException(
                "ERROR: unhandled backend type: " + str(backend_config.keys())
            )
        if origins:
            self.backend_acls.append(
                "    use_backend " + rule_id + " "
                "if { hdr(X-ORM-ID) -m str " + rule_id + " }"
            )
            self.backends.append("")
            self.backends.append("backend " + rule_id)
        for origin in origins:
            origin_instance = origin
            if isinstance(origin, str):
                origin_instance = {"server": origin}

            scheme, hostname, port = parser.extract_from_origin(
                origin_instance["server"]
            )
            server = (
                "    server "
                + parser.normalize(origin_instance["server"])
                + " "
                + hostname
                + ":"
                + port
                + " resolvers dns resolve-prefer ipv4"
                + " check"
            )
            if scheme == "https":
                # TODO: add 'verify required sni ca-file verifyhost'
                server += " ssl verify none"
            elif scheme != "http":
                raise ORMInternalRenderException(
                    "ERROR: unhandled origin " "scheme: " + scheme
                )
            if origin_instance.get("max_connections", False):
                server += " maxconn {}".format(origin_instance["max_connections"])

            if origin_instance.get("max_queued_connections", False):
                server += " maxqueue {}".format(
                    origin_instance["max_queued_connections"]
                )

            self.backends.append(server)

    def make_actions(self, action_config, rule_id):
        if "backend" in action_config:
            conf = action_config["backend"]
            self.make_backend_action(conf, rule_id)

    def __init__(self, rule_docs, globals_doc=None):
        super().__init__(
            rule_docs=rule_docs, globals_doc=globals_doc, output_file="haproxy.cfg"
        )
        self.backend_acls = []
        self.backends = []
        for rules in rule_docs.values():
            for rule in rules:
                self.make_actions(rule["actions"], rule["_rule_id"])

        crypto = self.globals_doc.get("crypto", {})
        certs = crypto.get("certificates", [])
        custom_internal_healthcheck = make_custom_internal_healthcheck(
            self.globals_doc.get("custom_internal_healthcheck", None)
        )
        internal_networks = self.globals_doc.get("internal_networks", [])
        dns = self.globals_doc.get("dns", {})
        nameservers = map(
            lambda x: x if ":" in x else x + ":53", dns.get("nameservers", [])
        )
        varnish = self.globals_doc.get("varnish", {})
        haproxy = self.globals_doc.get("haproxy", {})
        self.config = self.jinja.get_template("haproxy.cfg.j2").render(
            backend_acls=self.backend_acls,
            backends=self.backends,
            certs=certs,
            custom_internal_healthcheck=custom_internal_healthcheck,
            internal_networks=internal_networks,
            nameservers=nameservers,
            varnish_address=varnish.get("address", "localhost"),
            haproxy_address=haproxy.get("address", "localhost"),
            user=haproxy.get("user", "root"),
            group=haproxy.get("group", "root"),
            control_user=haproxy.get("control_user", "root"),
            control_group=haproxy.get("control_group", "root"),
        )
