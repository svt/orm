#!/bin/bash
/usr/sbin/varnishd \
    -F \
    -a :6081,PROXY \
    -a :6083,PROXY \
    -a :6084,PROXY \
    -a :6085,PROXY \
    -T localhost:6082 \
    -f /etc/varnish/default.vcl \
    -s malloc,256m
