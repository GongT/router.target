#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck source=shared.sh
source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/shared.sh"

cd "${STATE_DIRECTORY:-/var/lib/nftables}"

echo "using config file: ${CONFIG_FILE}"
nft --check # <-- will stop script if there is an error

DEBUG_MESSAGES=$(nft --check --debug eval 2>&1)

echo "${DEBUG_MESSAGES}" | grep -A1 'Evaluate flush'
if echo "${DEBUG_MESSAGES}" | grep -q 'Evaluate flush'; then
	TXT="$(echo "${DEBUG_MESSAGES}" | grep 'Evaluate flush' | sed -E 's/: Evaluate flush//g')"

	warn "$TXT"

	die "Deny use of 'flush' in rules."
fi

ADD_INFO=()
mapfile -t ADD_INFO < <(echo "${DEBUG_MESSAGES}" | sed -n '/Evaluate add/{n;p;}' | grep -E '^\s+table' | sed -E 's/^\s+//g; s/\s+/ /g' | sort | uniq)

echo "${#ADD_INFO[@]} tables found."
for LINE in "${ADD_INFO[@]}"; do
	FAMILY=$(echo "$LINE" | cut -d' ' -f2)
	NAME=$(echo "$LINE" | cut -d' ' -f3)
	if [[ $NAME == "{" ]]; then
		echo "$FAMILY" ## is name
	else
		echo "$FAMILY $NAME"
	fi
done >"${STATE_FILE}"

nft --echo
echo "Configuration applied successfully."
