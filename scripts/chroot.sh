#!/usr/bin/env bash

set -Eeuo pipefail

source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/inc/base.sh"

if [[ $# -eq 0 ]]; then
	set -- ash
fi

set -x
exec unshare --net --mount --mount-proc --pid --fork --propagation private "$SHELL" "$ROOT_DIR/scripts/tools/unshare.sh" "$@"
