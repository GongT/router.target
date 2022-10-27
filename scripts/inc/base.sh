#!/usr/bin/env bash

set -Eeuo pipefail

INIT_WD=$(pwd)
declare -xr INIT_WD
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

function die() {
	echo -e "\n\e[38;5;9m$*\e[0m" >&2
	exit 1
}

function info_warn() {
	echo -e "\e[38;5;11m$*\e[0m" >&2
}

function info_note() {
	echo -e "\e[2m$*\e[0m" >&2
}

source lowlevel.sh
source tempfile.sh
source exec.sh

cd ../..

ROOT_DIR=$(pwd)
declare -xr ROOT_DIR

# shellcheck source=../../config.default.sh
source config.default.sh
# shellcheck source=/dev/null
[[ -e config.sh ]] && source config.sh

declare -xr FS_DIR
declare -xr DATA_DIR
