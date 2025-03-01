#!/usr/bin/env bash

set -Eeuo pipefail

# shellcheck source=common/fn.sh
source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/common/fn.sh"

if [[ -L .config ]]; then
	unlink .config
fi
ln -s "$AppDataDir" .config

cat <<PROFILE >/etc/profile.d/router.sh
if ! [[ "\$PATH" = *"$ROOT_DIR/bin"* ]]; then
	export PATH="$ROOT_DIR/bin:\$PATH"
fi
PROFILE

NAMES=()
declare -xr DistBinaryDir="$ROOT_DIR/dist"
for F in assets/*.target assets/*.mount; do
	SRC="$ROOT_DIR/$F"
	name=$(basename "$SRC")
	DIST="$UNIT_ROOT/$name"
	NAMES+=("$name")

	echo "installing ${name} ..."
	DATA=$(<"$SRC")

	{
		echo "$DATA" | sed -s "s#\\\${DistBinaryDir}#$DIST_ROOT#g; s#\\\${PWD}#$(pwd)#g; s#\\\${AppDataDir}#${AppDataDir}#g; s#\\\${LocalConfigDir}#${LocalConfigDir}#g"
		echo ""
		echo "##### ROUTER GENERATED: source=$SRC"
	} >"$DIST"
done

mapfile -t FILES < <(find "$SERVICES_DIR" -maxdepth 2 -name install.sh)
for F in "${FILES[@]}"; do
	install_script "$F"
done

echo -e "\e[38;5;10mscript complete\e[0m"

systemctl daemon-reload

## enable all (no [install] will be ignore)
systemctl enable "${NAMES[@]}" "${REGISTERD_UNITS[@]}"

echo -e "\e[38;5;10mDone.\e[00m"
