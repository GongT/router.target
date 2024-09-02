#!/usr/bin/env bash

set -Eeuo pipefail

if [[ ! ${STATE_DIRECTORY-} ]]; then
	echo 'missing $STATE_DIRECTORY variable' >&2
	exit 1
fi

declare -r SRC="/var/lib/tlds/tlds-alpha-by-domain.txt"
if ! [[ -f ${SRC} ]]; then
	echo "missing $SRC" >&2
	exit 1
fi

echo "reading $SRC"
if ! [[ -d $STATE_DIRECTORY ]]; then
	mkdir "$STATE_DIRECTORY"
fi
cd "$STATE_DIRECTORY"

lines=$'################################\n'
lines+='# This file is created by: '
lines+="$(realpath "${BASH_SOURCE[0]}")"
lines+=$'\n'
lines+=$'################################\n\n'

while read -r line; do
	if [[ $line == "cn" ]]; then
		continue
	fi
	lines+="server=/$line/::1#8805"
	lines+=$'\n'
done < <(sed '/^#/d' /var/lib/tlds/tlds-alpha-by-domain.txt | tr '[:upper:]' '[:lower:]')

echo "write to $(pwd)/tlds.conf"
echo "$lines" >tlds.conf
