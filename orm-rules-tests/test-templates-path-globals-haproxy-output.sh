#!/bin/bash
EXP="# TEMPLATE_GLOBALS_TEST_MARKER"
CFG="/etc/haproxy/haproxy.cfg"
echo ""
echo "$0"
echo " # Testing for expected marker in config from haproxy template."
if ! egrep -q "$EXP" "$CFG"; then
  echo " ERROR. Could not find expected marker in haproxy.cfg,"
  echo "        from template."
  echo " Expected line matching regexp: $EXP"
  exit 1
else
  echo " OK. Found expected marker in haproxy.cfg"
fi
echo ""
