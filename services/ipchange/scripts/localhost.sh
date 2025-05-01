mapfile -t IP_LIST < <(hostname --all-ip-addresses | tr ' ' '\n' | grep -v '^$')

ip_is() {
	local VER="$1" IP="$2"
	ipcalc --check "-$VER" "$IP" &>/dev/null
}
