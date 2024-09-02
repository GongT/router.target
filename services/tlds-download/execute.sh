#!/usr/bin/env bash

#########################################
### download file: https://data.iana.org/TLD/tlds-alpha-by-domain.txt
### to /var/lib/tlds/tlds-alpha-by-domain.txt
#########################################

set -Eeuo pipefail

echo "\$STATE_DIRECTORY=${STATE_DIRECTORY-}"
STATE_DIR="${STATE_DIRECTORY:-/var/lib/tlds}"
if ! [[ -d $STATE_DIR ]]; then
	mkdir "$STATE_DIR"
fi

cd "$STATE_DIR"
echo "download to $STATE_DIR"

while ! wget -O "tlds-alpha-by-domain.txt" "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"; do
	sleep 1
done
