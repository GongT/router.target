#!/usr/bin/env bash

set -Eeuo pipefail

/usr/bin/cp -fvr /run/config/lower/. /run/config/upper/. /etc/ppp

ls -Al /etc/ppp

exec /usr/sbin/pppd call isp
