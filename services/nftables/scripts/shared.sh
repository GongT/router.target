shopt -s inherit_errexit extglob nullglob globstar lastpipe shift_verbose

MY_DIR="$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"
STATE_DIRECTORY="${STATE_DIRECTORY:-/var/lib/nftables}"

if [[ -t 2 ]]; then
	die() {
		printf "\e[38;5;9m%s\e[0m\n\n" "$*" >&2
		exit 1
	}
	info() {
		printf "\e[38;5;14m%s\e[0m\n" "$*" >&2
	}
	error() {
		printf "\e[38;5;9m%s\e[0m\n" "$*" >&2
	}
	warn() {
		printf "\e[38;5;11m%s\e[0m\n" "$*" >&2
	}
else
	die() {
		printf "[critical] %s\n\n" "$*" >&2
		exit 1
	}
	info() {
		printf "[info] %s\n" "$*" >&2
	}
	error() {
		printf "[error] %s\n" "$*" >&2
	}
	warn() {
		printf "[warn] %s\n" "$*" >&2
	}
fi

cd "${STATE_DIRECTORY}" || {
	mkdir "${STATE_DIRECTORY}"
	cd "${STATE_DIRECTORY}" || {
		die "Missing state directory: ${STATE_DIRECTORY}"
	}
}

if [[ $# -ne 1 ]]; then
	die "Usage: $0 <nftables config file name>"
fi

declare -r TABLE="${1}"
CONFIG_LIST=("${EXTRA_CONFIG_PATH:-/data/AppData/router/firewall}/${TABLE}.nft"
	"${MY_DIR}/configs/${TABLE}.nft"
)
STATED="${STATE_DIRECTORY}/${TABLE}"
mkdir -p "${STATED}"
chmod 0777 "${STATED}"

find "${STATED}" -name '*.nft' -type f -print0 | while IFS= read -r -d '' FILE; do
	CONFIG_LIST+=("$FILE")
done

CONFIG_FILE="${STATE_DIRECTORY}/${TABLE}.nft"

echo "flush table inet ${TABLE};" >"${CONFIG_FILE}"
echo "table inet ${TABLE} {" >>"${CONFIG_FILE}"

for FILE in "${CONFIG_LIST[@]}"; do
	if [[ -f $FILE ]]; then
		printf 'include "%s";\n' "${FILE}" >>"${CONFIG_FILE}"
	fi
done

echo "}" >>"${CONFIG_FILE}"
unset FILE TRIED_PATHS TRY_FILES

NFT=$(command -v nft)
nft() {
	"${NFT}" --file "$CONFIG_FILE" "$@"
}

declare -r NFT CONFIG_FILE STATE_DIRECTORY
