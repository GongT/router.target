#!/usr/bin/env bash

set -Eeuo pipefail

if [[ -e /etc/profile.d/50-environment.sh ]]; then
	source /etc/profile.d/50-environment.sh
fi

function with_proxy() {
	if [[ ${PROXY+f} == f ]] && [[ ${https_proxy+f} != f ]]; then
		echo "using proxy: $PROXY"
		https_proxy="$PROXY" http_proxy="$PROXY" all_proxy="$PROXY" "$@"
	else
		echo "can not call with proxy: not set"
		return 1
	fi
}

if [[ -z ${STATE_DIRECTORY-} ]]; then
	export INPUT_FILE="/data/AppData/router/proxy/subscription.txt"
fi

if [[ -z ${STATE_DIRECTORY-} ]]; then
	export STATE_DIRECTORY='/var/lib/v2ray'
fi
echo "\$STATE_DIRECTORY=${STATE_DIRECTORY-}"
cd "$STATE_DIRECTORY"

function die() {
	echo -e "$1" >&2
	exit "${2:-1}"
}

function _wget() {
	echo "  >> wget $*" >&2
	wget "$@"
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
	# if wget --timeout=5 -4 "$url" -O "${fname}.downloading"; then
	#	echo "complete with proxy"
	# el
	if _wget --force-progress --timeout=5 "$url" -O "${fname}.downloading"; then
		echo "complete without proxy"
	elif [[ -f "${fname}.txt" ]]; then
		echo "[$fname] Failed to download. use old one."
		continue
	else
		die "[$fname] Failed to download."
	fi

	if base64 -d "${fname}.downloading" &>/dev/null; then
		echo "file is valid base64 encoded"
		DATA=$(base64 -d "${fname}.downloading")
		rm -f "${fname}.downloading"
	else
		echo "file is NOT valid base64 encoded"
		DATA=$(<"${fname}.downloading")
	fi
	write_if_change "${fname}.txt" "$DATA"
done <"$INPUT_FILE"

if [[ $SOME_CHANGED -eq 1 ]]; then
	echo "request proxy service to restart!"
	systemctl restart --no-block proxy.service || true
fi
