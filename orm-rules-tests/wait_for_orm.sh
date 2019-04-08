#!/bin/bash
# Using rule rules/orm_status.yml to verify that ORM and echo servers are up
set -e
IP=$(lxc list orm -c 4 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+")

function orm_is_down()
{
    local STATUS_CODE=$(curl -H 'host:test' -o /dev/null -s -w "%{http_code}" ${IP}/orm-status)
    [ ${STATUS_CODE} -ne 200 ]
}

while orm_is_down; do
    echo "Waiting for ORM and echo servers to come online..."
    sleep 1
done
