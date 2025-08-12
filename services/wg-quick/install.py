from pathlib import Path

from router.target import install_python_binary, systemd_override

systemd_override("wg-quick@.service", "create-dhcp/wg-quick-override.service")
install_python_binary(
    "wireguard-deploy", Path(__file__).parent.joinpath("bins/wireguard-deploy.py")
)
