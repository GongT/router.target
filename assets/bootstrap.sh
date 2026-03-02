#!/bin/sh

pushd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" &> /dev/null
export POETRY_VIRTUALENVS_PATH=/usr/local/libexec/router
export POETRY_VIRTUALENVS_PROMPT=router.target

SETTING_ID='"python.defaultInterpreterPath"'
SETTINGS_FILE=$(realpath "$(pwd)/../.vscode/settings.json")


PYTHON_BIN=$(poetry env info -e || true)
if [[ -z "$PYTHON_BIN" ]]; then
	poetry install --sync
fi
PYTHON_BIN=$(poetry env info -e)

SETTING="${SETTING_ID}: \"${PYTHON_BIN}\","
if ! grep -q "${SETTING}" "${SETTINGS_FILE}"; then
	sed -i "s|${SETTING_ID}:.*|${SETTING}|" "${SETTINGS_FILE}"
fi

popd &> /dev/null
exec "${PYTHON_BIN}" "${@}"
