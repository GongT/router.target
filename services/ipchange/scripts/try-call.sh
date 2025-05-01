#!/usr/bin/env bash

CWD="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

cd /tmp

for I in "${APP_DATA_DIR}/ipchange/$1.sh" "${CWD}/on-$1-change.sh"; do
	if [[ -f $I ]]; then
		echo "+ $I"
		bash "$I"
		R=$?
		if [[ $R -ne 0 ]]; then
			echo "return code $R for $I"
		fi
	else
		echo "- $I"
	fi
done

true
