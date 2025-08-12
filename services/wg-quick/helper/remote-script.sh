#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s inherit_errexit extglob nullglob globstar lastpipe shift_verbose

PRIV_KEY=''
PUB_KEY=''

echo "$PRIV_KEY" > /etc/wireguard/prikey
echo "$PUB_KEY" > /etc/wireguard/pubkey

{
	cat <<-EOF
		[Interface]
		PrivateKey = $PRIV_KEY
		Address = 10.0.0.1/24

		[Peer]
		PublicKey = $PUB_KEY
		AllowedIPs = 10.0.0.2/32
	EOF
} > "/etc/wireguard/${VPN_NAME}.conf"
