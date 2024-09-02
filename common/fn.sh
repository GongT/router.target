#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
LIBROOT_DIR=$(pwd)
ROOT_DIR=$(dirname "$LIBROOT_DIR")
SERVICES_DIR="$ROOT_DIR/services"

die() {
	echo "$*" >&2
	exit 1
}

# shellcheck source=../.env.sample
source "../.env.sample"
# shellcheck source=../.env.sample
source "../.env"

source constants.sh
source systemd.sh
source config-files.sh

cd "$ROOT_DIR"

function filter_file() {
	local SRC DATA
	SRC=$(realpath "$1")
	DATA=$(<"$SRC")

	echo "$DATA" \
		| sed -s "s#\\\${ROOT_DIR}#$ROOT_DIR#g" \
		| sed -s "s#\\\${DistBinaryDir}#$DIST_ROOT#g" \
		| sed -s "s#\\\${PWD}#$(pwd)#g" \
		| sed -s "s#\\\${__dirname}#$(dirname "$SRC")#g; s#\\\${__filename}#$SRC#g" \
		| sed -s "s#\\\${AppDataDir}#${AppDataDir}#g; s#\\\${LocalConfigDir}#${LocalConfigDir}#g"
	echo ""
	echo "##### ROUTER GENERATED: source=$SRC"
}
