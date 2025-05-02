import os

from router.target import (
    DIST_ROOT,
    execute_passthru,
    git_clone_or_pull,
    is_install,
    systemd_add_unit,
    systemd_override,
)

systemd_add_unit("miniupnpd.service")
systemd_override("nftables@miniupnpd.service", "require-nftables-dropin.service")

distBin = DIST_ROOT / "miniupnpd/usr/sbin/miniupnpd"
if not distBin.exists() or is_install:
    srcDir = git_clone_or_pull("https://github.com/miniupnp/miniupnp.git")
    srcDir = srcDir / "miniupnpd"
    execute_passthru(
        "./configure",
        "--ipv6",
        "--leasefile",
        "--vendorcfg",
        "--pcp-peer",
        "--portinuse",
        "--firewall=nftables",
        "--disable-fork",
        "--systemd",
        cwd=srcDir,
    )
    execute_passthru("make", "-j", cwd=srcDir)

    os.environ["PREFIX"] = str(DIST_ROOT / "miniupnpd")
    execute_passthru("make", "install", cwd=srcDir)
    del os.environ["PREFIX"]
