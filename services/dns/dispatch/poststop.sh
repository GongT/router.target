#!/usr/bin/env bash

set -Eeuo pipefail

echo "[poststop] quitting..."
nft delete table inet chinadns
