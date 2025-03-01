#!/usr/bin/env bash

set -Eeuo pipefail

echo "DHCP-SCRIPT: $*"

SOURCE=/run/leases/dhcp.leases
TARGET=/run/leases/hosts

mapfile -t LINES <"$SOURCE"

RESULT=''

for LINE in "${LINES[@]}"; do
	if ! [[ "$LINE" ]]; then
		continue
	fi

	TIME=$(echo "$LINE" | awk '{print $1}')
	if [[ $TIME == duid ]]; then
		continue
	fi

	MAC=$(echo "$LINE" | awk '{print $2}')
	IP4=$(echo "$LINE" | awk '{print $3}')
	NAME=$(echo "$LINE" | awk '{print $4}')
	IP6=$(echo "$LINE" | awk '{print $5}')

	if [[ $NAME == '*' ]]; then
		continue
	fi

	if [[ $IP4 != '*' ]]; then
		RESULT+="$IP4 $NAME"$'\n'
	fi
	if [[ $IP6 != '*' ]]; then
		RESULT+="$IP6 $NAME"$'\n'
	fi
done

echo "$RESULT" >"$TARGET"
