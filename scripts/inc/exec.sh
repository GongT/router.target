#!/usr/bin/env bash

function chroot_exec() {
	chroot "$FS_DIR" /usr/bin/env -i "$@"
}
