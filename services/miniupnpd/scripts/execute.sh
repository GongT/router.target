#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s inherit_errexit extglob nullglob globstar lastpipe shift_verbose

if [[ -z ${DIST_ROOT-} ]]; then
	DIST_ROOT=/usr/local/libexec/router/dist
fi

MINIUPNPD="${DIST_ROOT}/miniupnpd/usr/sbin/miniupnpd"
exec "${MINIUPNPD}" -D \
	-f "./miniupnpd.conf" \
	-p /run/miniupnpd/miniupnpd.pid \
	-u "$(systemd-id128 --uuid machine-id)"
