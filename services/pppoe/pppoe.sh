#!/usr/bin/env bash

set -Eeuo pipefail

systemd-notify --status="starting..."

logger --tag 'pppoe:main' 'remove old device if found'
ip link del ppp0 || true

cp -fr /run/config/lower/. /etc/ppp

username=xxxxxxxxxxxx
password=yyyyyyyyyyyy

CONFIG_FILE=/run/config/upper/auth.conf
if ! [[ -e $CONFIG_FILE ]]; then
	echo "username='$username'
password='$password'
" >"$CONFIG_FILE"
	echo "you must set username and password in auth.conf" >&2
	exit 233
fi
source "$CONFIG_FILE"

if [[ $username == "xxxxxxxxxxxx" ]]; then
	echo "you must set username and password in auth.conf" >&2
	exit 233
fi

AUTH="\"$username\" * \"$password\""
echo "$AUTH" >/etc/ppp/chap-secrets
echo "$AUTH" >/etc/ppp/pap-secrets

mkdir -p /etc/ppp/peers
cat <<-EOF >/etc/ppp/peers/isp
	nic-wan
	ifname ppp0
	user "$username"
	password "$password"
	set NOTIFY_SOCKET=$NOTIFY_SOCKET
EOF

logger --tag 'pppoe:main' </etc/ppp/options
logger --tag 'pppoe:main' </etc/ppp/peers/isp

systemd-notify --status="connecting..."
exec /usr/sbin/pppd call isp
