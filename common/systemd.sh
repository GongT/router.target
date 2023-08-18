REGISTERD_UNITS=()

function filter_file() {
	local SRC="$1"
	DATA=$(<"$SRC")

	echo "$DATA" \
		| sed -s "s#\\\${DistBinaryDir}#$DIST_ROOT#g" \
		| sed -s "s#\\\${PWD}#$(pwd)#g" \
		| sed -s "s#\\\${AppDataDir}#${AppDataDir}#g; s#\\\${LocalConfigDir}#${LocalConfigDir}#g"
	echo ""
	echo "##### ROUTER GENERATED: source=$SRC"
}

function systemd_install() {
	local -r TARGET="$UNIT_ROOT/$1"
	filter_file "$1" >"$TARGET"
	echo "  * systemd unit file: $TARGET"
}

function systemd_service() {
	systemd_install "$1"
	REGISTERD_UNITS+=("$1")
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

	echo "Installing $INIT_CWD:"
	pushd "$(dirname "$F")" &>/dev/null
	# shellcheck source=/dev/null
	source install.sh
	popd &>/dev/null
}
