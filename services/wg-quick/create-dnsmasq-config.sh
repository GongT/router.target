#!/usr/bin/env bash

set -Eeuo pipefail
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

echo "Create dns settings for interface $IF_NAME"

# IF_NAME
OUTPUT_FILE=$(realpath "../wireguard-dns/config/wg.$IF_NAME.leases.conf")
CONFIG_FILE="/etc/wireguard/$IF_NAME.conf"

echo "OUTPUT_FILE: $OUTPUT_FILE"

mapfile -t DOMAINS < <(networkctl status --json=short "$IF_NAME" | jq -c -M -r '.SearchDomains[].Domain')
echo "    DOMAINS: ${DOMAINS[*]}"

mapfile -t LINES < <(grep -E '^AllowedIPs' "$CONFIG_FILE")
for LINE in "${LINES[@]}"; do
	echo "FOR: $LINE"
	IFS='= ' read -r _ L <<<"$LINE"
	IFS='# ' read -r IP NAME <<<"$L"

	if ! [[ $IP ]] || ! [[ "$NAME" ]]; then
		continue
	fi
	echo "    IP='$IP', NAME='$NAME'"

	DATA+="address=/$NAME/$IP"$'\n'
	for DOMAIN in "${DOMAINS[@]}"; do
		if ! [[ $DOMAIN == ~* ]]; then
			DATA+="address=/$NAME.$DOMAIN/$IP"$'\n'
		fi
	done
done

if [[ $DATA != $(cat "$OUTPUT_FILE" || true) ]]; then
	echo "new leases file created"
	echo "$DATA" >"$OUTPUT_FILE"
	systemctl restart --no-block wireguard-dns.service
else
	echo "leases file not change."
fi
