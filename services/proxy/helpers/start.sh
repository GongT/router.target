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

rm -rf tmp/subscriptions
mkdir -p tmp/subscriptions
find "${STATE_DIRECTORY}/subscriptions" -type f -print | while read -r SUB_FILE; do
	echo "convert file: ${SUB_FILE}"
	BASE=$(basename "${SUB_FILE}" .txt)
	OUT="${STATE_DIRECTORY}/tmp/subscriptions/${BASE}.json"
	"${BINARY}" parse "${SUB_FILE}" --output "${OUT}" >/dev/null
	echo "  - ${OUT}"
done

echo ""
echo "creating config file: ${CONFIG_FILE}"
function create_cfg() {
	python3 "${__dirname}/subscription-filter.py" "${CONFIG_FILE}"
}

if ! create_cfg 2>/dev/null; then
	create_cfg || true
	exit 66
fi

# exec "${BINARY}" --directory "${STATE_DIRECTORY}" --config-directory "${CONFIG_FILE}" run --hiddify "${APP_CONFIG}"
