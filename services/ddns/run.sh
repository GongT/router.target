#!/usr/bin/env bash

set -Eeuo pipefail

WAN_DEV=ppp0
IPV4=
LASTUPDATE4=0
IPV6=
LASTUPDATE6=0
STATE_FILE="ddns-state.sh"
declare -i FORCE_TS=$(date +%s)
FORCE_TS=$((FORCE_TS - 43200))

if [[ ${DDNS_KEY+found} != found ]] || [[ ${DDNS_KEY+found} != found ]]; then
	source "/data/AppData/router/ddns/config.sh"
fi

function pecho() {
	echo -e "[DDNS] (ipv$NET_TYPE) $*" >&2
}

function x() {
	pecho " + $*"
	"$@"
}

function die() {
	pecho "\e[38;5;9m$*\e[0m"
	exit 66
}

function ddns_script() {
	local NET_TYPE=$1 IP_ADDR=$2 TYPE BODY

	if [[ $NET_TYPE == 6 ]]; then
		TYPE=AAAA
	else
		TYPE=A
	fi

	local RECORD_ID_NAME="CF_RECORD_ID$NET_TYPE"
	local RECORD_ID=${!RECORD_ID_NAME}

	BODY=$(
		jq -n '{"type":$TYPE,"name":$HOST_NAME,"content":$IP_ADDR,"ttl":300,"proxied":false,"comment":"DDNS@router"}' \
			--arg TYPE "$TYPE" \
			--arg IP_ADDR "$IP_ADDR" \
			--arg HOST_NAME "$HOST_NAME"
	)

	pecho "request update api..."
	x curl --no-progress-meter -X PUT "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records/${RECORD_ID}" \
		-H "Authorization: Bearer ${CF_TOKEN}" \
		-H "Content-Type: application/json" \
		--data "$BODY" \
		--output "$RUNTIME_DIRECTORY/output.json"

	jq '.' "$RUNTIME_DIRECTORY/output.json"

	local ret
	ret=$(jq '.success' "$RUNTIME_DIRECTORY/output.json")
	if [[ $ret != 'true' ]]; then
		die "failed update"
	else
		pecho "successfull update"
	fi

	pecho "update done."
}

function load() {
	if ! [[ -e $STATE_FILE ]]; then
		return
	fi

	local _IPV4 _LASTUPDATE4 _IPV6 _LASTUPDATE6

	source "$STATE_DIRECTORY/$STATE_FILE" || {
		echo "invalid variable file: $STATE_DIRECTORY/$STATE_FILE" >&2
		echo "some variable will not load" >&2
	}

	IPV4=${_IPV4:-''}
	LASTUPDATE4=${_LASTUPDATE4:-'0'}
	IPV6=${_IPV6:-''}
	LASTUPDATE6=${_LASTUPDATE6:-'0'}
}
function save() {
	{
		echo "_IPV4=$(printf %q "$IPV4")"
		echo "_LASTUPDATE4=$(printf %q "$LASTUPDATE4")"
		echo "_IPV6=$(printf %q "$IPV6")"
		echo "_LASTUPDATE6=$(printf %q "$LASTUPDATE6")"
	} >"$STATE_DIRECTORY/$STATE_FILE"
}

echo "STATE_DIRECTORY=$STATE_DIRECTORY"
echo "RUNTIME_DIRECTORY=$RUNTIME_DIRECTORY"
cd "$STATE_DIRECTORY"
load

### IPV4
export NET_TYPE=4
IP=$(ip addr show dev "$WAN_DEV" | grep ' inet ' | grep 'scope global' | head -n1 | ip addr show dev "$WAN_DEV" | grep ' inet ' | grep 'scope global' | grep -oP '\b([0-9]+\.){3}[0-9]+\b' | head -n1 || true)

if [[ ! $IP ]]; then
	die "missing IPv4 on WAN interface"
fi

ipcalc --check --ipv4 "$IP"

pecho "interface IP: $IP"
if [[ $IP == "$IPV4" ]] && [[ $LASTUPDATE4 -gt $FORCE_TS ]]; then
	pecho "address not changed (update at $(date "--date=@$LASTUPDATE4" '+%Y-%m-%d %H:%M:%S'))"
else
	pecho "address change from ${IPV4-} to $IP"

	ddns_script 4 "$IP"

	IPV4=$IP
	LASTUPDATE4=$(date +%s)
	save
fi

### IPV6
export NET_TYPE=6
IP=$(ip addr show dev "$WAN_DEV" | grep ' inet6 ' | grep ' scope global ' | grep ' dynamic ' | grep -oP '\b[0-9a-f:]{10,}(?=/)' | head -n1 || true)

if [[ ! $IP ]]; then
	pecho "\e[38;5;11mmissing IPv6 on WAN interface\e[0m"
	exit 0
fi

ipcalc --check --ipv6 "$IP"

pecho "interface IP: $IP"
if [[ $IP == "$IPV6" ]] && [[ $LASTUPDATE4 -gt $FORCE_TS ]]; then
	pecho "address not changed (update at $(date "--date=@$LASTUPDATE4" '+%Y-%m-%d %H:%M:%S'))"
else
	pecho "address change from ${IPV6-} to $IP"

	ddns_script 6 "$IP"

	IPV6=$IP
	LASTUPDATE6=$(date +%s)
	save
fi
