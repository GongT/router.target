#!/usr/bin/bash
# https://raw.githubusercontent.com/alecthw/chnlist/release/mosdns/whitelist.list

ROUTER_DATA_PATH=/data/AppData/router

FILE="/tmp/whitelist.list"
OUT_FILE="${ROUTER_DATA_PATH}/dns/dispatch/force.china.autolist"


mapfile -t LINES < "$FILE"

for LINE in "${LINES[@]}"; do
	# Skip empty lines and comments
	if [[ -z "$LINE" || "$LINE" =~ ^# ]] ; then
		continue
	fi
	if [[ "$LINE" == keyword:* ]] ; then
		continue
	fi

	if [[ "$LINE" == domain:* ]] ; then
		DOMAIN="${LINE#domain:}"
	elif [[ "$LINE" == full:* ]] ; then
		DOMAIN="${LINE#full:}"
	else
		echo "skip: $LINE">&2
		continue
	fi

	echo "$DOMAIN" 
done > "${OUT_FILE}"

echo "ok: $OUT_FILE"
