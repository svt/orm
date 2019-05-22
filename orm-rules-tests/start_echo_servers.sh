#!/bin/bash
set -xe

lxc file push orm-rules-tests/echo_server.py orm/root/
lxc file push orm-rules-tests/49-haproxy.conf orm/etc/rsyslog.d/
lxc file push \
    orm-rules-tests/echo_server@.service \
    orm/etc/systemd/system/echo_server@.service
lxc exec orm systemctl restart rsyslog
lxc exec orm systemctl restart haproxy
lxc exec orm systemctl daemon-reload
lxc exec orm systemctl restart echo_server@7357
lxc exec orm systemctl restart echo_server@7358
lxc exec orm systemctl restart echo_server@7359
# Used as domain_default backend
lxc exec orm systemctl restart echo_server@1337
