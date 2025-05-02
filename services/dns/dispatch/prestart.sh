#!/usr/bin/env bash

set -Eeuo pipefail

echo "[prestart] loading"
WD="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"


echo "[prestart] make config file"
cat "${LIBEXEC_ROOT}/dns/dispatch-config" >"${STATE_DIRECTORY}/chinadns-config"

echo "[prestart] ensure config folder"
cd "${APP_DATA_DIR}/dns/dispatch"

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
