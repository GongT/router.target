#!/usr/bin/env bash

set -Eeuo pipefail

source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/inc/base.sh"

INIT_PID=$(machinectl show openwrt | grep -E '^Leader=' | grep -oE '[0-9]+') || die "failed find procd"
info_note "PID=$INIT_PID"

if ! [[ $INIT_PID ]]; then
	die "init process (procd) not found"
fi

if [[ $# -eq 0 ]]; then
	set -- ash
fi

nsenter --target "$INIT_PID" --all /usr/bin/env -i "${@}"
