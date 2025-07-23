from router.target import install_python_binary, systemd_add_unit

systemd_add_unit("service/proxy-subscription-update.service")
systemd_add_unit("service/proxy-subscription-update.timer")

install_python_binary("proxy-subscription-pull", "cli/proxy-subscription-pull.py")
