#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s inherit_errexit extglob nullglob globstar lastpipe shift_verbose

if [[ -z ${ROOT_DIR-} ]]; then
	ROOT_DIR="$(realpath -m "${BASH_SOURCE[0]}/../../../../")"
fi


MINIUPNPD="${ROOT_DIR}/dist/miniupnpd/usr/sbin/miniupnpd"
exec "${MINIUPNPD}" -D \
	-f "./miniupnpd.conf" \
	-p /run/miniupnpd/miniupnpd.pid \
	-u "$(systemd-id128 --uuid machine-id)"
