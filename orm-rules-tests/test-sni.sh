#!/bin/bash
EXP="server 127_0_0_1 127.0.0.1:443 .*check-sni test sni str\(test\)"

CFG="/etc/haproxy/haproxy.cfg"
echo ""
echo "$0"
echo " # Testing for rendered 'check-sni' and 'sni' parameters"
if ! egrep -q "$EXP" "$CFG"; then
  echo " ERROR. Could not find expected 'check-sni' and 'sni' parameters in haproxy.cfg,"
  echo "        configured in 'test_sni.yml'."
  echo " Expected line matching regexp: $EXP"
  exit 1
else
  echo " OK. Found expected parameters in haproxy.cfg"
fi
echo ""
