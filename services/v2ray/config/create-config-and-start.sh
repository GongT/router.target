#!/usr/bin/env bash

set -Eeuo pipefail

__dirname="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

echo "\$STATE_DIRECTORY=$STATE_DIRECTORY"
cd "$STATE_DIRECTORY"

echo "creating config file"
function create_cfg() {
	python3 "${__dirname}/create-config.py"
}
if ! create_cfg 2>/dev/null; then
	create_cfg || true
	exit 66
fi

ARGS=(
	"${__dirname}/prefix.json"
	"/tmp/config.json"
	"${AppDataDir}/proxy/v2config.json"
	"${__dirname}/postfix.json"
)

CARGS=()
for arg in "${ARGS[@]}"; do
	CARGS+=("-c" "$arg")
done

V2RAY="${ROOT_DIR:-/opt}/dist/v2ray/v2ray"

echo "config test."
if "${V2RAY}" test "${CARGS[@]}"; then
	"${V2RAY}" convert "${ARGS[@]}" | jq --tab > effective.json

	echo "Start with config file: $(pwd)/effective.json"
	exec "${V2RAY}" run -c "effective.json"
else
	echo "error!"
	exit 66
fi
