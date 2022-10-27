#!/bin/ash

set -e
UCI=$(command -v uci)

if ! "$UCI" show network >/dev/null 2>&1; then
	touch /etc/config/network
fi

if ! "$UCI" show network.lan >/dev/null 2>&1; then
	"$UCI" set network.lan=interface
	"$UCI" set network.lan.device='br-lan'
	"$UCI" set network.lan.proto='static'
	"$UCI" set network.lan.ipaddr='192.168.90.1'
	"$UCI" set network.lan.netmask='255.255.255.0'
	"$UCI" set network.lan.ip6assign='60'
	"$UCI" set network.lan.defaultroute='0'
fi

if ! "$UCI" show network.wan >/dev/null 2>&1; then
	"$UCI" set network.wan=interface
	"$UCI" set network.wan.proto='dhcp'
fi

find_section() {
	CONFIG=$1 SECTION=$2 FIELD=$3 MATCH=$4

	"$UCI" show "$CONFIG" | grep ".@$SECTION" | grep ".$FIELD=" | grep "$MATCH" | grep -o '.*]'
}

BR_LAN=$(find_section network device name br-lan || true)
if ! [ "$BR_LAN" ]; then
	BR_LAN="network.$("$UCI" add network device)"
	"$UCI" set "${BR_LAN}.name=br-lan"
	"$UCI" set "${BR_LAN}.type=bridge"
	"$UCI" set "${BR_LAN}.bridge_empty=1"
	"$UCI" set "${BR_LAN}.mtu=9000"
fi

for IF in $IF_LIST; do
	echo "processing $IF"

	"$UCI" del_list "${BR_LAN}.ports=$IF"
	"$UCI" add_list "${BR_LAN}.ports=$IF"

	DEVICE=$(find_section network device name "$IF" || true)
	if ! [ "$DEVICE" ]; then
		BR_LAN="network.$("$UCI" add network device)"
		"$UCI" set "${BR_LAN}.name=$IF"
		"$UCI" set "${BR_LAN}.mtu=9000"
	fi
done
"$UCI" commit

echo "All Done."
