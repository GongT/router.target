#!/usr/bin/env bash

set -Eeuo pipefail

__dirname="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

if [[ -z ${STATE_DIRECTORY-} ]]; then
	export STATE_DIRECTORY='/var/lib/proxy'
fi
echo "STATE_DIRECTORY='${STATE_DIRECTORY-}'"
cd "$STATE_DIRECTORY"

export CONFIG_FILE="${STATE_DIRECTORY}/subscription.json"
BINARY="${DIST_ROOT}/sing-box/sing-box"

x() {
	echo "$*" >&2
	"$@"
}

echo ""
echo "creating config file: ${CONFIG_FILE}"
function create_cfg() {
	x python3 "${__dirname}/create-config-file.py"
}
function process_list() {
	x python3 "${__dirname}/convert-user-lists.py"
}

if ! create_cfg || ! process_list; then
	echo "!!!failed generate config file!!!"
	exit 66
fi

x exec "${BINARY}" --disable-color --directory "${STATE_DIRECTORY}" --config "${CONFIG_FILE}" run
