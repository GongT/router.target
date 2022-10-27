#!/usr/bin/env bash

set -Eeuo pipefail

source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/inc/base.sh"

pwd
{
	echo -n 'IF_LIST="'
	(cd /sys/class/net && find . -follow -mindepth 1 -maxdepth 1 -type d)
	echo '"'

	cat scripts/tools/init-network.sh
} | ./scripts/chroot.sh ash
