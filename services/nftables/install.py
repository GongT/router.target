from pathlib import Path

from router.target import ROUTER_DATA_PATH, systemd_add_unit, write_if_change

systemd_add_unit("nftables@.service")

write_if_change(
    Path("/etc/sysconfig/nftables.conf"),
    """### This file is replaced by router.target
### use nftables@xxx.service instead

""",
)

firewall_config_dir = ROUTER_DATA_PATH / "firewall"
firewall_config_dir.mkdir(parents=True, exist_ok=True)
