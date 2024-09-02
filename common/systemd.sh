REGISTERD_UNITS=()

function systemd_add_unit() {
	local INSTALL_NAME SOURCE
	INSTALL_NAME="$(basename "$1")"

	local -r TARGET="$UNIT_ROOT/$INSTALL_NAME"
	if [[ ${2+found} == found ]]; then
		SOURCE="$2"
	elif [[ -e $1 ]]; then
		SOURCE="$1"
	else
		die "missing systemd unit file"
	fi

	if [[ $SOURCE == *.service ]] && ! grep -qF "Slice=router.slice" "$SOURCE"; then
		die "missing Slice= in $SOURCE"
	fi

	filter_file "$SOURCE" >"$TARGET"
	echo "  * systemd unit file: $(basename "$SOURCE") -> $TARGET"
	REGISTERD_UNITS+=("$INSTALL_NAME")
}

function systemd_override() {
	local -r SOURCE=$2 TARGET="/etc/systemd/system/$1.d/router-override.conf"
	mkdir -p "/etc/systemd/system/$1.d"
	echo "  * systemd override file: $TARGET"
	filter_file "$SOURCE" >"$TARGET"
}

function install_script() {
	local F=$1 INIT_CWD
	INIT_CWD=$(dirname "$F")

	echo "Installing $(basename "$INIT_CWD"):"
	pushd "$(dirname "$F")" &>/dev/null
	# shellcheck source=/dev/null
	source install.sh
	popd &>/dev/null
}
