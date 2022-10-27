#!/usr/bin/env bash

set -Eeuo pipefail

source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/inc/base.sh"

TARGET=$(curl -s https://downloads.openwrt.org/ | grep --max-count=1 -oE "releases/.+/targets") || die "failed index openwrt version"
info_note "target: $TARGET"

VERSION=${TARGET#*/}
VERSION=${VERSION%/*}

URL="https://downloads.openwrt.org/$TARGET/x86/64/openwrt-$VERSION-x86-64-generic-ext4-rootfs.img.gz"
info_note "url: $URL"

mkdir -p cache

if ! [[ -e "cache/${VERSION}.img.gz" ]]; then
	wget --continue -O "cache/${VERSION}.img.gz.downloading" --progress=bar "$URL"
	mv "cache/${VERSION}.img.gz.downloading" "cache/${VERSION}.img.gz"
fi

gunzip --keep --force "cache/${VERSION}.img.gz"

ROOTFS=$(mktemp -d)
mount "cache/${VERSION}.img" "$ROOTFS"
function umount_it() {
	umount "$ROOTFS"
}
register_exit_handler umount_it

mkdir -p "$FS_DIR/tmp"
rm -rf "$FS_DIR"/tmp/*

INSTALLED_PACKAGES=()
if [[ -e "$FS_DIR/bin/opkg" ]]; then
	mkdir -p "$FS_DIR/var/lock"
	mapfile -t INSTALLED_PACKAGES < <(chroot_exec opkg list-installed | awk '{print $1}')

	rm -f cache/installed-packages.lst
	for I in "${INSTALLED_PACKAGES[@]}"; do
		echo "$I" >>cache/installed-packages.lst
	done
	info_note "remember ${#INSTALLED_PACKAGES[@]} packages"
fi

mkdir -p "$DATA_DIR/config"
if ! [[ -e "$DATA_DIR/config/system" ]]; then
	info_note "first install, copy config files"
	cp -vr "$ROOTFS/etc/config/." "$DATA_DIR/config"
fi

rm -rf "$ROOTFS/etc/config"
cp -rf "$ROOTFS/." "$FS_DIR"
for I in dev proc sys etc/config; do
	mkdir -p "$FS_DIR/$I"
	chattr +i "$FS_DIR/$I"
done
for I in rom overlay lost+found; do
	rm -rf "$FS_DIR/$I"
done

if [[ ${#INSTALLED_PACKAGES[@]} -gt 0 ]]; then
	info_note "restore ${#INSTALLED_PACKAGES[@]} packages"
	chroot_exec opkg install "${INSTALLED_PACKAGES[@]}"
fi
