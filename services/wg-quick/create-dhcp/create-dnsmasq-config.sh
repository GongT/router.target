#!/usr/bin/env bash

set -Eeuo pipefail
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

echo "Create dns settings for interface $IF_NAME"

# IF_NAME
OUTPUT_FILE="$STATE_DIRECTORY/hosts"
CONFIG_FILE="/etc/wireguard/$IF_NAME.conf"

echo "OUTPUT_FILE: $OUTPUT_FILE"

mapfile -t DOMAINS < <(networkctl status --json=short "$IF_NAME" | jq -c -M -r '.SearchDomains[].Domain')
echo "    DOMAINS: ${DOMAINS[*]}"

FDOMAINS=()
for DOMAIN in "${DOMAINS[@]}"; do
	if ! [[ $DOMAIN == ~* ]]; then
		FDOMAINS+=("$DOMAIN")
	fi
done
echo "    FDOMAINS: ${FDOMAINS[*]}"

mapfile -t LINES < <(grep -E '^AllowedIPs' "$CONFIG_FILE")
for LINE in "${LINES[@]}"; do
	echo "FOR: $LINE"
	IFS='= ' read -r _ L <<<"$LINE"
	IFS='# ' read -r IP NAME <<<"$L"

	if ! [[ $IP ]] || ! [[ "$NAME" ]]; then
		continue
	fi
	echo "    IP='$IP', NAME='$NAME'"

	DATA+="$IP"
	for DOMAIN in "${FDOMAINS[@]}"; do
		DATA+=" $NAME.$DOMAIN"
	done
	DATA+=$'\n'
done

if [[ $DATA != $(cat "$OUTPUT_FILE" || true) ]]; then
	echo "new leases file created"
	echo "$DATA" >"$OUTPUT_FILE"
else
	echo "leases file not change."
fi
