#!/bin/bash
EXP="server http_127_0_0_1_7359 127.0.0.1:7359 .*maxconn 2 maxqueue 3"
CFG="/etc/haproxy/haproxy.cfg"
echo ""
echo "$0"
echo " # Testing for rendered 'maxconn' and 'maxqueue' parameters"
if ! egrep -q "$EXP" "$CFG"; then
  echo " ERROR. Could not find expected 'maxconn' and 'maxqueue' parameters in haproxy.cfg,"
  echo "        configured in 'test_backend_maxconn_maxqueue.yml'."
  echo " Expected line matching regexp: $EXP"
  exit 1
else
  echo " OK. Found expected parameters in haproxy.cfg"
fi
echo ""
