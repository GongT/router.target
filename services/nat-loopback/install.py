from router.target import systemd_add_unit

systemd_add_unit("natloopback.service")
systemd_add_unit("natloopback.path")
