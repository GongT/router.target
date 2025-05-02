#!/usr/bin/env python3

import os
from pathlib import Path

from router.target import (
    APP_DATA_DIR,
    LIBEXEC_ROOT,
    ROOT_DIR,
    UNIT_ROOT,
    TimestampFile,
    cleanup_and_enable_services,
    ensure_symlink,
    execute_output,
    execute_passthru,
    execute_python_script,
    logger,
    set_pyenv,
    set_working_directory,
    systemd_add_unit,
    write_if_change,
)

set_working_directory(ROOT_DIR)

ensure_symlink(ROOT_DIR / ".config", APP_DATA_DIR)
ensure_symlink(APP_DATA_DIR / "firewalld", Path("/etc/firewalld"))
ensure_symlink(APP_DATA_DIR / "systemd", Path("/etc/systemd"))
ensure_symlink(ROOT_DIR / ".outputs/units", UNIT_ROOT)
ensure_symlink(ROOT_DIR / ".outputs/assets", LIBEXEC_ROOT)

if "VIRTUAL_ENV" in os.environ:
    del os.environ["VIRTUAL_ENV"]

os.environ["POETRY_VIRTUALENVS_PATH"] = LIBEXEC_ROOT.as_posix()
os.environ["POETRY_VIRTUALENVS_PROMPT"] = "(router.target) "

write_if_change(
    Path("/etc/profile.d/router.sh"),
    f"""
if ! [[ "$PATH" = *"{ROOT_DIR}/bin"* ]]; then
	export PATH="{ROOT_DIR}/bin:$PATH"
fi
""",
)

LIBEXEC_ROOT.mkdir(exist_ok=True, parents=True)
ts = TimestampFile(LIBEXEC_ROOT / "last_install_pyenv", 60 * 60 * 12)
if ts.is_expired():
    execute_passthru("poetry", "install", "--no-root", "--sync")
else:
    logger.dim("pyenv is up to date, skipping poetry install (--force to update)")

ts.update()

env_dir = execute_output("poetry", "env", "info", "--path")
set_pyenv(env_dir)

for file in ROOT_DIR.joinpath("assets").glob("*"):
    systemd_add_unit(file.as_posix())

for subabs in ROOT_DIR.joinpath("services").iterdir():
    logger.dim(f"> {subabs.relative_to(ROOT_DIR)}")

    set_working_directory(subabs)

    installer = subabs / "install.py"
    if installer.exists():
        execute_python_script(installer)
    else:
        logger.warning(f"installer not found!")


logger.success("script complete")

cleanup_and_enable_services()
logger.success("Done.")
