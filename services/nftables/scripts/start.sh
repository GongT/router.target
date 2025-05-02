#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck source=shared.sh
source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/shared.sh"

cd "${STATE_DIRECTORY:-/var/lib/nftables}"

echo "using config file: ${CONFIG_FILE}"
nft --file "${CONFIG_FILE_FLUSHED}" --check
# <-- will stop script if there is an error

DEBUG_MESSAGES=$(nft --check --debug eval --file "${CONFIG_FILE}" 2>&1)

## TODO: filter delete
if [[ "${DEBUG_MESSAGES}" == *'Evaluate flush'* ]]; then
	TXT="$(echo "${DEBUG_MESSAGES}" | grep 'Evaluate flush' | sed -E 's/: Evaluate flush//g')"

	warn "$TXT"

	die "Deny use of 'flush' in rules."
else
	echo "No 'flush' found in rules."
fi

nft --file "${CONFIG_FILE_FLUSHED}" --echo
echo "Configuration applied successfully."
