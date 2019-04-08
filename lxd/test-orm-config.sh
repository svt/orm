#!/bin/bash
set -e

if [ "$#" -ne 1 ]; then
    echo "Usage $0 orm/rules/glob"
    exit 1
fi

RULES_GLOB="$1"

IP=$(lxc list orm -c 4 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+")

set -x
orm --test-target "$IP" \
    --test-target-insecure \
    --orm-rules-path "$RULES_GLOB" \
    --no-check
