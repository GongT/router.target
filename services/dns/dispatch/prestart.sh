#!/usr/bin/env bash

set -Eeuo pipefail

echo "[prestart] loading"
WD="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

# shellcheck source=common/fn.sh
source "$ROOT_DIR/common/fn.sh"

echo "[prestart] make config file"
filter_file "${WD}/files/config-template" >"${STATE_DIRECTORY}/chinadns-config"

echo "[prestart] ensure config folder"
cd "${AppDataDir}/dns/dispatch"

function ensure() {
	if [[ ! -e $1 ]]; then
		touch "$1"
	fi
}
ensure "hosts"
ensure "config"
ensure "force.china.list"
ensure "force.oversea.list"
ensure "blacklist.list"

echo "[prestart] update nftables"

if ! [[ -e "/var/lib/nftables/router/chinadns-ng.nft" ]]; then
	mkdir -p /var/lib/nftables/router
	touch "/var/lib/nftables/router/chinadns-ng.nft"
fi
nft -f "${WD}/files/chinadns-ng.nft"

echo "[prestart] success!"
