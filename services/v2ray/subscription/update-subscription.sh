#!/usr/bin/env bash

set -Eeuo pipefail

if [[ -e /etc/profile.d/50-environment.sh ]]; then
	source /etc/profile.d/50-environment.sh
fi
if [[ ${PROXY+f} == f ]] && [[ ${https_proxy+f} != f ]]; then
	echo "using proxy: $PROXY"
	export https_proxy="$PROXY" http_proxy="$PROXY" all_proxy="$PROXY"
fi

echo "\$STATE_DIRECTORY=${STATE_DIRECTORY-}"
cd "$STATE_DIRECTORY"

function die() {
	echo -e "$1" >&2
	exit "${2:-1}"
}

declare -i SOME_CHANGED=0
function write_if_change() {
	local FNAME="$1" DATA="$2" OLD_DATA
	if [[ -e $FNAME ]]; then
		OLD_DATA=$(<"$FNAME")
		if [[ $OLD_DATA == "$DATA" ]]; then
			echo "$FNAME unchanged"
			return
		fi
	fi

	echo "emit file $FNAME"
	echo -n "$DATA" >"$FNAME"
	SOME_CHANGED=1
}

if ! [[ -e $INPUT_FILE ]]; then
	die "missing input file at $INPUT_FILE" 66
fi

mkdir -p subscriptions
cd subscriptions

echo "reading from $INPUT_FILE"
while read -r LINE; do
	if [[ -z $LINE ]] || [[ $LINE == "#"* ]]; then
		continue
	fi
	if [[ $LINE != *" "* ]]; then
		die "\tinvalid line: $LINE\n\texpected format: NAME https://xxxx" 66
	fi
done <"$INPUT_FILE"

while read -r LINE; do
	if [[ -z $LINE ]] || [[ $LINE == "#"* ]]; then
		continue
	fi

	fname=$(echo "$LINE" | cut -d' ' -f1)
	url=$(echo "$LINE" | cut -d' ' -f2)

	echo "[$fname] Downloading from: $url"
	if wget "$url" -O "${fname}.downloading"; then
		:
	elif wget --no-proxy "$url" -O "${fname}.downloading"; then
		:
	elif [[ -f "${fname}.txt" ]]; then
		echo "[$fname] Failed to download. use old one."
		continue
	else
		die "[$fname] Failed to download."
	fi

	if base64 -d "${fname}.downloading" &>/dev/null; then
		DATA=$(base64 -d "${fname}.downloading")
	else
		DATA=$(<"${fname}.downloading")
	fi
	write_if_change "${fname}.txt" "$DATA"
done <"$INPUT_FILE"

if [[ $SOME_CHANGED -eq 1 ]]; then
	echo "request proxy service to restart!"
	systemctl restart --no-block proxy.service || true
fi
