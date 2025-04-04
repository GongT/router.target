#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s inherit_errexit extglob nullglob globstar lastpipe shift_verbose

nft add table inet miniupnpd
nft add chain inet miniupnpd forward '{ type filter hook forward priority filter; }'
nft add chain inet miniupnpd prerouting '{ type nat hook prerouting priority dstnat; }'
nft add chain inet miniupnpd postrouting '{ type nat hook postrouting priority srcnat; }'

touch /var/lib/miniupnpd/leases
