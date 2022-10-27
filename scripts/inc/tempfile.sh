#!/usr/bin/env bash

if [[ ${TMPDIR:-} ]]; then
	declare -xr TMPDIR="$TMPDIR/router.target"
elif [[ ${XDG_RUNTIME_DIR:-} ]]; then
	declare -xr TMPDIR="$XDG_RUNTIME_DIR/router.target"
else
	declare -xr TMPDIR="/tmp/router.target"
fi
info_note "tempdir: $TMPDIR"

function __exit_delete_temp_files() {
	if [[ $EXIT_CODE -eq 0 ]]; then
		rm -rf "$TMPDIR"
	elif [[ -e $TMPDIR ]]; then
		info_warn "exit with error, not deleting temp files: $TMPDIR"
	fi
}

MKTEMP=$(command -v mktemp)
_TEMPD_CREATED=
function mktemp() {
	if ! [[ $_TEMPD_CREATED ]]; then
		rm -rf "$TMPDIR"
		mkdir -p "$TMPDIR"
		_TEMPD_CREATED=yes
		register_exit_handler __exit_delete_temp_files
	fi
	"$MKTEMP" "$@"
}
