#!/bin/bash
set -e

if [ "$#" -ne 1 ] || [ ! -d "$1" ]; then
    echo "Usage $0 path/to/orm/config/directory"
    exit 1
fi

set -x

CONFIG_DIR="$1"

lxc file push $CONFIG_DIR/haproxy.cfg orm/etc/haproxy/haproxy.cfg
lxc file push $CONFIG_DIR/varnish.vcl orm/etc/varnish/varnish.vcl
lxc exec orm -- systemctl restart haproxy
lxc exec orm -- bash -c "if (varnishadm vcl.list | grep -q orm-rules); then (varnishadm vcl.use boot && varnishadm vcl.discard orm-rules); fi"
lxc exec orm -- varnishadm vcl.load orm-rules /etc/varnish/varnish.vcl
lxc exec orm -- varnishadm vcl.use orm-rules
