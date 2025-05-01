#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s inherit_errexit extglob nullglob globstar lastpipe shift_verbose

systemctl --no-block restart ddns.service ipsets-generation.service
