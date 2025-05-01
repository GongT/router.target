#!/usr/bin/env bash

set -Eeuo pipefail

echo "[poststop] quitting..."

{
	nft list set inet router chnip4
	nft list set inet router gfwip4
	nft list set inet router chnip6
	nft list set inet router gfwip6
} | grep -Ev '^table ' | grep -Ev '^}$' >"/var/lib/nftables/router/chinadns-ng.nft"
echo "[poststop] nftables config saved to /var/lib/nftables/router/chinadns-ng.nft"
