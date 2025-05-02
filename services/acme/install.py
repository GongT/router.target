from router.target import (
    APP_DATA_DIR,
    ROOT_DIR,
    execute_passthru,
    git_clone_or_pull,
    systemd_add_unit,
)

systemd_add_unit("acme-renew.timer")
systemd_add_unit("acme-renew.service")

acme_source_dir = git_clone_or_pull("https://github.com/acmesh-official/acme.sh.git")
execute_passthru(
    "./acme.sh",
    "--install",
    "--home",
    f"{ROOT_DIR}/dist/acme.sh",
    "--config-home",
    f"{APP_DATA_DIR}/ACME",
    "--cert-home",
    f"{APP_DATA_DIR}/ACME/certs",
    "--accountkey",
    f"{APP_DATA_DIR}/ACME/account.key",
    "--accountconf",
    f"{APP_DATA_DIR}/ACME/account.conf",
    "--useragent",
    "router.target/acme(https://github.com/gongt/router.target)",
    "--nocron",
    "--no-profile",
    cwd=acme_source_dir,
)
