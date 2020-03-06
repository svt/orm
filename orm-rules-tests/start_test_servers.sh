#!/bin/bash
set -xe

lxc file push orm-rules-tests/echo_server.py orm/root/
lxc file push orm-rules-tests/slow_server.py orm/root/
lxc file push \
    orm-rules-tests/*@.service \
    orm/etc/systemd/system/

lxc exec orm systemctl daemon-reload
lxc exec orm systemctl restart echo_server@7357
lxc exec orm systemctl restart echo_server@7358
lxc exec orm systemctl restart echo_server@7359
# Used as domain_default backend
lxc exec orm systemctl restart echo_server@1337
# Start slow_server for timeout tests
lxc exec orm systemctl restart slow_server@4242
