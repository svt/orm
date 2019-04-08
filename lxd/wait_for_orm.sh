#!/bin/bash
lxc exec orm -- bash -c "until (ping -c1 archive.ubuntu.com &>/dev/null); do echo Waiting for network...; sleep 1; done"
