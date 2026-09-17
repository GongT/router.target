#!/usr/bin/env bash

set -Eeuo pipefail

LIBEXEC_ROOT=${LIBEXEC_ROOT:-/usr/local/libexec/router}

#shellcheck source=/usr/local/libexec/router/acme.sh/environment.sh
source "${LIBEXEC_ROOT}/acme.sh/environment.sh"

acme "$@"
