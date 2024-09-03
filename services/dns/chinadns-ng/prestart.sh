#!/usr/bin/env bash

set -Eeuo pipefail

echo "[prestart] loading"

# shellcheck source=common/fn.sh
source "$ROOT_DIR/common/fn.sh"

echo "[prestart] make config file"
filter_file config/chinadns-ng/config >"${STATE_DIRECTORY}/chinadns-config"

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
nft add table inet global
nft add set inet global chnip4 '{ type ipv4_addr; flags interval; }'
nft add set inet global chnip6 '{ type ipv6_addr; flags interval; }'

nft add set inet global gfwip4 '{ type ipv4_addr; flags interval; }'
nft add set inet global gfwip6 '{ type ipv6_addr; flags interval; }'

echo "[prestart] success!"
