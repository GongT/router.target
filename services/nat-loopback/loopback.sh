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
	local DATA OLD_DATA FILE="$1"
	OLD_DATA=$(<"/etc/firewalld/policies/$FILE.xml")
	DATA+="$(echo "$OLD_DATA" | sed '/<rule/,/<\/rule>/d' | head -n-1)"
	DATA+=$'\n\n'
	DATA+="$RULES"
	DATA+='</policy>'

	if [[ $OLD_DATA == "$DATA" ]]; then
		echo "$FILE not change"
		return
	fi

	CHANGE=yes

	local OLD_FILE="/etc/firewalld/policies/$FILE.xml.old" NEW_FILE="/etc/firewalld/policies/$FILE.xml"
	echo "$FILE file changed"
	rm -f "$OLD_FILE"
	mv "$NEW_FILE" "$OLD_FILE"
	echo "$DATA" >"$NEW_FILE"
}

handle ipv4-loopback-1
handle ipv4-loopback-2

if [[ $CHANGE == yes ]]; then
	firewall-cmd --reload
fi
