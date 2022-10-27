#!/usr/bin/env bash

set -Eeuo pipefail

set -x
mkdir -p "$FS_DIR/etc/config"
mount --bind "$DATA_DIR/config" "$FS_DIR/etc/config"
mkdir -p "$FS_DIR/data"
mount --bind "$DATA_DIR/data" "$FS_DIR/data"
mount --bind "/proc" "$FS_DIR/proc"
mount -t devtmpfs devtmpfs "$FS_DIR/dev"
mount -t devpts devpts "$FS_DIR/dev/pts"

exec chroot "$FS_DIR" /usr/bin/env -i "$@"
