#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
LIBROOT_DIR=$(pwd)
ROOT_DIR=$(dirname "$LIBROOT_DIR")

die() {
	echo "$*" >&2
	exit 1
}

# shellcheck source=../.env.sample
source "../.env.sample"
# shellcheck source=../.env.sample
source "../.env"

source constants.sh

cd "$ROOT_DIR"
