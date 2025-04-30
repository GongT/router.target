#!/usr/bin/env bash

set -Eeuo pipefail

mapfile -t LINES < <(grep forward-port /etc/firewalld/policies/ipv4-NAT.xml | sed 's/^[[:space:]]*//g')

CHANGE=no

RULES=''
for L in "${LINES[@]}"; do
	RULES+=$'  <rule family="ipv4">\n'
	RULES+=$'    <destination ipset="wan-4" />\n'
	RULES+="    ${L}"$'\n'
	RULES+=$'  </rule>\n'
done

handle() {
	local DATA OLD_DATA='' FILE="$1" FPATH="/etc/firewalld/policies/$1.xml"
	if [[ -e $FPATH ]]; then
		OLD_DATA=$(<"$FPATH")
	fi
	DATA+="$(echo "$OLD_DATA" | sed '/<rule/,/<\/rule>/d' | head -n-1)"
	DATA+=$'\n\n'
	DATA+="$RULES"
	DATA+='</policy>'

	if [[ $OLD_DATA == "$DATA" ]]; then
		echo "$FILE not change"
		return
	fi
	echo "$FILE file changed"

	CHANGE=yes

	local OLD_FILE="/etc/firewalld/policies/$FILE.xml.old"
	rm -f "$OLD_FILE"

	if [[ -e $FPATH ]]; then
		mv "$FPATH" "$OLD_FILE"
	fi

	echo "$DATA" >"$FPATH"
}

handle ipv4-loopback-1
handle ipv4-loopback-2

if [[ $CHANGE == yes ]]; then
	firewall-cmd --reload
fi
