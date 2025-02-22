#!/usr/bin/env bash

set -Eeuo pipefail

__dirname="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

if [[ -z ${STATE_DIRECTORY-} ]]; then
	export STATE_DIRECTORY='/var/lib/proxy'
fi
echo "STATE_DIRECTORY='${STATE_DIRECTORY-}'"
cd "$STATE_DIRECTORY"

export CONFIG_FILE="${STATE_DIRECTORY}/subscription.json"
BINARY="${ROOT_DIR:-/opt}/dist/sing-box"
APP_CONFIG="${ROOT_DIR:-/opt}/services/sing-box/config/config.json"

echo ""
echo "creating config file: ${CONFIG_FILE}"
function create_cfg() {
	python3 "${__dirname}/create-config-file.py" "${CONFIG_FILE}"
	python3 "${__dirname}/convert-user-lists.py"
}

if ! create_cfg &>/dev/null; then
	create_cfg || true

	echo "!!!failed generate config file!!!"
	exit 66
fi

exec "${BINARY}" --directory "${STATE_DIRECTORY}" --config "${CONFIG_FILE}" run
