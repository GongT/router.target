from pathlib import Path

from router.target import (
    ROUTER_DATA_PATH,
    LIBEXEC_ROOT,
    execute_passthru,
    git_clone_or_pull,
    systemd_add_unit,
    user_agent,
    stringify_shell_variables,
)

systemd_add_unit("acme-renew.timer")
systemd_add_unit("acme-renew.service")

acme_source_dir = git_clone_or_pull("https://github.com/acmesh-official/acme.sh.git")
acme_dist_dir = Path(f"{LIBEXEC_ROOT}/acme.sh")

envs = {
    "LE_WORKING_DIR": acme_dist_dir.as_posix(),
    "LE_CONFIG_HOME": f"{ROUTER_DATA_PATH}/ACME",
    "DEFAULT_CA": "letsencrypt",
    "DEFAULT_LOG_FILE": "/var/log/acme.log",
    "USER_AGENT": user_agent,
    "HOME": acme_dist_dir.as_posix(),
    "CERT_HOME": f"{ROUTER_DATA_PATH}/ACME/certs",
}

execute_passthru(
    "./acme.sh",
    "--install",
    "--useragent",
    user_agent,
    "--nocron",
    "--no-profile",
    cwd=acme_source_dir,
    addenv=envs
)

envText= f"""
{stringify_shell_variables({"ROUTER_DATA_PATH":ROUTER_DATA_PATH.as_posix()}, 'export')}
function acme {{
    {stringify_shell_variables(envs, verb="/usr/bin/env")} bash "{acme_dist_dir}/acme.sh" "$@"
}}
"""

acme_dist_dir.joinpath("environment.sh").write_text(envText)
