#!/usr/bin/env bash

set -Eeuo pipefail

DDNS_HOST=
DDNS_KEY=''
source /data/AppData/router/ddns/config.sh

function pecho() {
	echo "[DDNS] (ipv$NET_TYPE) $*" >&2
}

function x() {
	pecho " + $*"
	"$@"
}

function die() {
	pecho "\e[38;5;9m$*\e[0m"
	exit 1
}

function ddns_script() {
	pecho "request update api..."
	while true; do
		sleep 1
		if x /usr/bin/curl --no-progress-meter "-$NET_TYPE" "https://dyn.dns.he.net/nic/update" \
			-d "hostname=${DDNS_HOST}" \
			-d "password=${DDNS_KEY}"; then
			break
		fi
	done
	pecho ""
	pecho "update done."
}

function save() {
	local NAME=$1 VALUE=$2 DATA

	if [[ -e ddns-history.txt ]]; then
		DATA=$(grep -v "$NAME=" ddns-history.txt || true)
	fi

	{
		echo "$DATA"
		echo $'\n'
		echo "$NAME='$VALUE'"
	} | tee ddns-history.txt
}

echo "STATE_DIRECTORY=$STATE_DIRECTORY"
cd "$STATE_DIRECTORY"

if [[ -e ddns-history.txt ]]; then
	source ddns-history.txt || die "invalid variable file: $(pwd)ddns-history.txt" >&2
fi

### IPV4
export NET_TYPE=4
IP=$(ip addr show dev router-pppoe | grep ' inet ' | grep 'scope global' | head -n1 | ip addr show dev router-pppoe | grep ' inet ' | grep 'scope global' | grep -oP '\b([0-9]+\.){3}[0-9]+\b' | head -n1 || true)

if [[ ! $IP ]]; then
	die "missing IPv4 on WAN interface"
fi

ipcalc --check --ipv4 "$IP"

pecho "interface IP: $IP"
if [[ "${IPV4:-}" ]] && [[ $IP == "$IPV4" ]]; then
	pecho "address not changed"
else
	pecho "address change from ${IPV4:-} to $IP"

	ddns_script 4

	save IPV4 "$IP"
fi

### IPV6
export NET_TYPE=6
IP=$(ip addr show dev br-lan | grep ' inet6 ' | grep ' scope global ' | grep ' dynamic ' | grep -oP '\b[0-9a-f:]{10,}(?=/)' | head -n1 || true)

if [[ ! $IP ]]; then
	pecho "\e[38;5;11mmissing IPv6 on WAN interface\e[0m"
	exit 0
fi

ipcalc --check --ipv6 "$IP"

pecho "interface IP: $IP"
if [[ "${IPV6:-}" ]] && [[ $IP == "$IPV6" ]]; then
	pecho "address not changed"
else
	pecho "address change from ${IPV6:-} to $IP"

	ddns_script 6

	save IPV6 "$IP"
fi
