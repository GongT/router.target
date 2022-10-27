#!/usr/bin/env bash

set -Eeuo pipefail

die() {
	echo -e "\e[38;5;9m$*\e[0m" >&2
	exit 1
}

if [[ $(id -u) -ne 0 ]]; then
	set -x
	exec sudo "$SHELL" "$0" "$@"
fi

cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

declare -xr NODEJS_ROOT="$(pwd)/.data/nodejs"
declare -xr NODEJS_BIN="$(pwd)/.data/nodejs/bin/node"
mkdir -p "$NODEJS_ROOT"

function _wget() {
	if wget --help 2>&1 | grep -q -- '--show-progress'; then
		wget --continue --quiet --show-progress --progress=bar "$1" -O "$2"
	else
		wget -c -q "$1" -O "$2"
	fi
}

function download_file() {
	local url="$1" save_at DOWNLOAD="$2"
	save_at="$DOWNLOAD/$(basename "${url}")"

	echo "Download file from $url:"
	echo "    to: $save_at"

	_wget "$url" "${save_at}.downloading" || die "Cannot download."
	mv "${save_at}.downloading" "${save_at}"

	echo "    saved at ${save_at}"
}

install_nodejs() {
	local INSTALL_VERSION="v18.10.0"
	echo "Installing nodejs:"
	download_file "https://nodejs.org/dist/$INSTALL_VERSION/node-$INSTALL_VERSION-linux-x64.tar.gz" "$NODEJS_ROOT"
	tar xf "$NODEJS_ROOT/node-$INSTALL_VERSION-linux-x64.tar.gz" --strip-components=1 -C "$NODEJS_ROOT"
}

if ! [[ -e $NODEJS_BIN ]]; then
	install_nodejs
fi

"$NODEJS_BIN" --version

export PATH="$NODEJS_ROOT/bin:$PATH"

npm --global install pnpm
pnpm install

pnpm run build

pnpm run install-script
