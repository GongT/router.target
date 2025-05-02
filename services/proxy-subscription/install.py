from router.target import systemd_add_unit

systemd_add_unit("service/proxy-subscription-update.service")
systemd_add_unit("service/proxy-subscription-update.timer")
