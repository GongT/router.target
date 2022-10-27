#!/usr/bin/env bash

declare -a EXIT_HANDLERS=()
function register_exit_handler() {
	EXIT_HANDLERS+=("$@")
}
function _exit() {
	local EXIT_CODE=$?
	set +Eeuo pipefail
	local CB
	for CB in "${EXIT_HANDLERS[@]}"; do
		# echo -e "\e[2m  * $CB\e[0m" >&2
		"$CB"
	done

	if [[ $EXIT_CODE -ne 0 ]]; then
		info_note "\nscript exit with code $EXIT_CODE"
		callstack 1
	fi

	exit $EXIT_CODE
}

trap _exit EXIT

function callstack() {
	local -i SKIP=${1-1}
	local -i i
	if [[ ${#FUNCNAME[@]} -le $SKIP ]]; then
		info_note "  * empty callstack *"
	fi
	for i in $(seq "$SKIP" $((${#FUNCNAME[@]} - 1))); do
		if [[ ${BASH_SOURCE[$((i + 1))]+found} == "found" ]]; then
			info_note "  $i: ${BASH_SOURCE[$((i + 1))]}:${BASH_LINENO[$i]} ${FUNCNAME[$i]}()"
		else
			info_note "  $i: ${FUNCNAME[$i]}()"
		fi
	done
}
