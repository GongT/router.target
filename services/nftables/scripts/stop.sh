#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck source=shared.sh
source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/shared.sh"

if ! [[ -f ${STATE_FILE} ]]; then
	warn "State file does not exist."
	exit 0
fi

echo "deleting table: $TABLE"
nft --echo destroy table "$TABLE" || true

echo "Configuration removed successfully."
