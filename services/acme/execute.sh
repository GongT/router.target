#!/usr/bin/env bash

set -Eeuo pipefail

source "${ROOT_DIR}/dist/acme.sh/acme.sh.env"

acme.sh --upgrade
acme.sh --cron --debug
