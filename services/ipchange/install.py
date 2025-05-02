from pathlib import Path
from shutil import copy

from router.target import (
    execute_mute,
    execute_output,
    install_directory,
    systemd_add_unit,logger
)

systemd_add_unit("ipchange-monitor.service")
systemd_add_unit("ipchange@.service")
systemd_add_unit("ipchange.service")
systemd_add_unit("ipsets-generate.service", "ipsets-generation/ipsets-generate.service")

__dirname = Path(__file__).parent

current = execute_output("firewall-offline-cmd", "--get-ipsets", ignore=True).split(" ")

install_directory(
    __dirname / "firewalld-template-ipsets",
    Path("/etc/firewalld/ipsets"),
)

CHANGED = False
for TYPE in ["wan", "localhost", "lan"]:
    for INET in ["4", "6"]:
        if f"{TYPE}{INET}" not in current:
            logger.dim(f"  - create firewalld ipset: {TYPE}{INET}")
            CHANGED = True

if CHANGED:
    execute_mute("firewall-cmd", "--reload", ignore=True)
