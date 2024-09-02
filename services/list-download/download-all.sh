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
STATE_DIR="${STATE_DIRECTORY:-/var/lib/lists}"
if ! [[ -d $STATE_DIR ]]; then
	mkdir "$STATE_DIR"
fi

declare -a FLIST=()

function download() {
	local NAME="$1" URL="$2"
	local DONE_FILE="${STATE_DIR}/${NAME}.downloaded"
	local TMP_FILE="/tmp/${NAME}.downloading"
	FLIST+=("$NAME")

	echo "downloading: $URL"

	if [[ -e ${DONE_FILE} ]]; then
		echo "    exists: ${DONE_FILE}"
		return
	fi
	wget -O "${TMP_FILE}" "${URL}"
	echo "download ok: ${DONE_FILE}"
	cat "${TMP_FILE}" >"${STATE_DIR}/${NAME}"
	mv "${TMP_FILE}" "${DONE_FILE}"
}

download gfwlist.txt 'https://raw.githubusercontent.com/pexcn/daily/gh-pages/gfwlist/gfwlist.txt'
download accelerated-domains.china.conf 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf'
download apple.china.conf 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/apple.china.conf'
download google.china.conf 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/google.china.conf'
download bogus-nxdomain.china.conf 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/bogus-nxdomain.china.conf'
download chnroute.txt 'https://raw.githubusercontent.com/pexcn/daily/gh-pages/chnroute/chnroute.txt'
download chnroute6.txt 'https://raw.githubusercontent.com/pexcn/daily/gh-pages/chnroute/chnroute6.txt'
download apnic.list 'https://ftp.apnic.net/stats/apnic/delegated-apnic-latest'

cd "$STATE_DIR"
for NAME in "${FLIST[@]}"; do
	mv "${NAME}.downloaded" "$NAME"
done
echo "All files downloaded."

# https://github.com/zfl9/chinadns-ng/blob/master/res/update-chnlist.sh
cat "accelerated-domains.china.conf" "apple.china.conf" | grep -v -e '^[[:space:]]*$' -e '^[[:space:]]*#' | awk -F/ '{print $2}' | sort | uniq >"chnlist.txt"

echo "Generator done."
