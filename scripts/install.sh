#!/usr/bin/env bash

set -Eeuo pipefail

source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/inc/base.sh"

function filter_args() {
	sed "s#{DATA_DIR}#$DATA_DIR#g" \
		| sed "s#{FS_DIR}#$FS_DIR#g" \
		| sed "s#{ROOT_DIR}#$ROOT_DIR#g"
}

filter_args <assets/openwrt.nspawn >"${FS_DIR}.nspawn"
filter_args <assets/openwrt.service >/usr/lib/systemd/system/openwrt.service
filter_args <assets/router.target >/usr/lib/systemd/system/router.target

systemctl daemon-reload
systemctl enable openwrt.service

systemctl cat router.target

systemctl cat openwrt.service

info_warn "files saved, use: systemctl enable --now router.target"
